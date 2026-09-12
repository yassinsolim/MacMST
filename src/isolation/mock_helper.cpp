#include "isolation/mock_helper.hpp"

#include <algorithm>
#include <cerrno>
#include <csignal>
#include <fcntl.h>
#include <poll.h>
#include <spawn.h>
#include <sys/wait.h>
#include <unistd.h>

namespace macmst::isolation {
namespace {

class FileDescriptor {
public:
    FileDescriptor() = default;
    ~FileDescriptor() { reset(); }
    FileDescriptor(const FileDescriptor&) = delete;
    FileDescriptor& operator=(const FileDescriptor&) = delete;
    int get() const { return value_; }
    void reset(int value = -1) {
        if (value_ >= 0) {
            close(value_);
        }
        value_ = value;
    }

private:
    int value_ = -1;
};

bool make_pipe(FileDescriptor& reader, FileDescriptor& writer) {
    int descriptors[2] {-1, -1};
    if (pipe(descriptors) != 0) {
        return false;
    }
    reader.reset(descriptors[0]);
    writer.reset(descriptors[1]);
    for (FileDescriptor* descriptor : {&reader, &writer}) {
        if (descriptor->get() <= STDERR_FILENO) {
            const int duplicate = fcntl(descriptor->get(), F_DUPFD_CLOEXEC, STDERR_FILENO + 1);
            if (duplicate < 0) {
                return false;
            }
            descriptor->reset(duplicate);
        }
        if (fcntl(descriptor->get(), F_SETFD, FD_CLOEXEC) != 0) {
            return false;
        }
    }
    const int flags = fcntl(reader.get(), F_GETFL);
    return flags >= 0 && fcntl(reader.get(), F_SETFL, flags | O_NONBLOCK) == 0;
}

int drain(FileDescriptor& descriptor, std::span<std::uint8_t> output,
          std::size_t& size, std::size_t& observed) {
    std::array<std::uint8_t, 256> buffer {};
    for (unsigned int attempt = 0; descriptor.get() >= 0 && attempt < 4; ++attempt) {
        const ssize_t count = read(descriptor.get(), buffer.data(), buffer.size());
        if (count > 0) {
            const auto received = static_cast<std::size_t>(count);
            const auto retained = std::min(received, output.size() - size);
            std::copy_n(buffer.begin(), retained, output.begin() + static_cast<std::ptrdiff_t>(size));
            size += retained;
            observed += received;
            if (observed > output.size()) {
                return 0;
            }
        } else if (count == 0) {
            descriptor.reset();
        } else if (errno == EAGAIN || errno == EWOULDBLOCK) {
            return 0;
        } else if (errno != EINTR) {
            return errno;
        }
    }
    return 0;
}

}

MockResult run_mock_helper(const char* executable, std::string_view scenario,
    std::chrono::milliseconds deadline, std::chrono::milliseconds reap_grace) {
    using Clock = std::chrono::steady_clock;
    const auto started = Clock::now();
    MockResult result;
    const auto finish = [&]() {
        result.elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - started);
        return result;
    };
    const auto selected = std::find(mock_scenarios.begin(), mock_scenarios.end(), scenario);
    if (executable == nullptr || executable[0] != '/' || selected == mock_scenarios.end() ||
        deadline.count() < 1 || deadline.count() > 10000 || reap_grace.count() < 1 || reap_grace.count() > 10000) {
        return finish();
    }
    const std::string_view executable_path(executable);
    if (executable_path.size() > 4096 || executable_path.substr(executable_path.find_last_of('/') + 1) != "macmst_mock_helper") {
        return finish();
    }
    FileDescriptor stdout_reader;
    FileDescriptor stdout_writer;
    FileDescriptor stderr_reader;
    FileDescriptor stderr_writer;
    if (!make_pipe(stdout_reader, stdout_writer) || !make_pipe(stderr_reader, stderr_writer)) {
        result.outcome = MockOutcome::IoFailure;
        result.system_error = errno;
        return finish();
    }
    posix_spawn_file_actions_t actions;
    posix_spawnattr_t attributes;
    int error = posix_spawn_file_actions_init(&actions);
    if (error != 0) {
        result.outcome = MockOutcome::SpawnFailure;
        result.system_error = error;
        return finish();
    }
    error = posix_spawnattr_init(&attributes);
    if (error != 0) {
        posix_spawn_file_actions_destroy(&actions);
        result.outcome = MockOutcome::SpawnFailure;
        result.system_error = error;
        return finish();
    }
    sigset_t empty_mask;
    sigset_t defaults;
    sigemptyset(&empty_mask);
    sigemptyset(&defaults);
    for (int signal_number : {SIGABRT, SIGTERM, SIGINT, SIGPIPE, SIGCHLD}) {
        sigaddset(&defaults, signal_number);
    }
    const short flags = static_cast<short>(POSIX_SPAWN_CLOEXEC_DEFAULT | POSIX_SPAWN_SETSIGMASK | POSIX_SPAWN_SETSIGDEF);
    const auto record_error = [&](int status) {
        if (error == 0) {
            error = status;
        }
    };
    record_error(posix_spawnattr_setflags(&attributes, flags));
    record_error(posix_spawnattr_setsigmask(&attributes, &empty_mask));
    record_error(posix_spawnattr_setsigdefault(&attributes, &defaults));
    record_error(posix_spawn_file_actions_addopen(&actions, STDIN_FILENO, "/dev/null", O_RDONLY, 0));
    record_error(posix_spawn_file_actions_adddup2(&actions, stdout_writer.get(), STDOUT_FILENO));
    record_error(posix_spawn_file_actions_adddup2(&actions, stderr_writer.get(), STDERR_FILENO));
    for (int descriptor : {stdout_reader.get(), stdout_writer.get(), stderr_reader.get(), stderr_writer.get()}) {
        record_error(posix_spawn_file_actions_addclose(&actions, descriptor));
    }
    std::array<char*, 3> arguments {const_cast<char*>(executable), const_cast<char*>(selected->data()), nullptr};
    char locale[] = "LC_ALL=C";
    std::array<char*, 2> environment {locale, nullptr};
    if (error == 0) {
        ++result.spawn_attempts;
        error = posix_spawn(&result.pid, executable, &actions, &attributes, arguments.data(), environment.data());
    }
    posix_spawnattr_destroy(&attributes);
    posix_spawn_file_actions_destroy(&actions);
    stdout_writer.reset();
    stderr_writer.reset();
    if (error != 0) {
        result.outcome = MockOutcome::SpawnFailure;
        result.system_error = error;
        result.pid = 0;
        return finish();
    }
    const auto operation_deadline = Clock::now() + deadline;
    auto cleanup_deadline = operation_deadline;
    const auto fail = [&](MockOutcome outcome) {
        if (!result.failure_trigger.has_value()) {
            result.failure_trigger = outcome;
            result.outcome = outcome;
            cleanup_deadline = Clock::now() + reap_grace;
        }
    };
    for (;;) {
        for (int io_error : {
            drain(stdout_reader, result.stdout_bytes, result.stdout_size, result.stdout_observed),
            drain(stderr_reader, result.stderr_bytes, result.stderr_size, result.stderr_observed)}) {
            if (io_error != 0) {
                result.system_error = io_error;
                fail(MockOutcome::IoFailure);
            }
        }
        if (result.stdout_observed > mock_frame_size || result.stderr_observed > result.stderr_bytes.size()) {
            fail(MockOutcome::OutputLimit);
        } else if (result.stdout_size == mock_frame_size &&
                   !parse_mock_response({result.stdout_bytes.data(), result.stdout_size}).has_value()) {
            fail(MockOutcome::ProtocolFailure);
        }
        if (!result.reaped) {
            int wait_status = 0;
            const pid_t waited = waitpid(result.pid, &wait_status, WNOHANG);
            if (waited == result.pid) {
                result.reaped = true;
                result.wait_status = wait_status;
            } else if (waited < 0 && errno != EINTR) {
                result.system_error = errno;
                result.outcome = MockOutcome::ReapFailure;
                return finish();
            }
        }
        if (!result.failure_trigger.has_value() && Clock::now() >= operation_deadline) {
            fail(MockOutcome::Timeout);
        }
        if (result.reaped && stdout_reader.get() < 0 && stderr_reader.get() < 0) {
            if (!result.failure_trigger.has_value()) {
                if (!WIFEXITED(*result.wait_status) || WEXITSTATUS(*result.wait_status) != 0) {
                    result.outcome = MockOutcome::AbnormalExit;
                } else {
                    result.mock_ior_return = parse_mock_response({result.stdout_bytes.data(), result.stdout_size});
                    result.outcome = !result.mock_ior_return.has_value() ? MockOutcome::ProtocolFailure :
                        *result.mock_ior_return == 0 ? MockOutcome::Success : MockOutcome::OperationFailure;
                }
            }
            return finish();
        }
        if (result.failure_trigger.has_value() && !result.reaped && !result.termination_sent) {
            result.termination_sent = true;
            if (kill(result.pid, SIGKILL) != 0) {
                result.termination_error = errno;
            }
        }
        if (result.failure_trigger.has_value() && Clock::now() >= cleanup_deadline) {
            if (!result.reaped) {
                result.outcome = MockOutcome::ReapTimeout;
            }
            return finish();
        }
        const auto remaining = std::chrono::duration_cast<std::chrono::milliseconds>(
            (result.failure_trigger.has_value() ? cleanup_deadline : operation_deadline) - Clock::now()).count();
        const int wait_ms = static_cast<int>(std::clamp<std::int64_t>(remaining, 1, 10));
        std::array<pollfd, 2> descriptors {{{stdout_reader.get(), POLLIN, 0}, {stderr_reader.get(), POLLIN, 0}}};
        if (poll(descriptors.data(), static_cast<nfds_t>(descriptors.size()), wait_ms) < 0 && errno != EINTR) {
            result.system_error = errno;
            fail(MockOutcome::IoFailure);
        }
    }
}

}