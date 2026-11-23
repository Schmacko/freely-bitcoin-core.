// Copyright (c) 2026-present The FREELY contributors
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

// Standalone parallel SHA-256d miner for a fully specified 80-byte FREELY
// genesis header. It does not choose or modify consensus parameters.

#include <openssl/sha.h>

#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <cstdint>
#include <cstring>
#include <exception>
#include <iomanip>
#include <iostream>
#include <mutex>
#include <sstream>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>

namespace {
constexpr uint64_t NONCE_LIMIT = uint64_t{1} << 32;
using Bytes32 = std::array<unsigned char, 32>;
using HeaderPrefix = std::array<unsigned char, 76>;

Bytes32 ParseHex32(const std::string& hex)
{
    if (hex.size() != 64) throw std::invalid_argument("expected exactly 64 hexadecimal characters");
    Bytes32 out{};
    auto nibble = [](char c) -> unsigned char {
        if (c >= '0' && c <= '9') return c - '0';
        if (c >= 'a' && c <= 'f') return c - 'a' + 10;
        if (c >= 'A' && c <= 'F') return c - 'A' + 10;
        throw std::invalid_argument("invalid hexadecimal character");
    };
    for (size_t i = 0; i < out.size(); ++i) out[i] = (nibble(hex[2 * i]) << 4) | nibble(hex[2 * i + 1]);
    return out;
}

uint64_t ParseUnsigned(const std::string& value, int base = 10)
{
    if (value.empty() || value.front() == '-') {
        throw std::invalid_argument("expected a non-negative integer");
    }

    size_t offset{0};
    if (base == 0) {
        base = 10;
        if (value.size() >= 2 && value[0] == '0' && (value[1] == 'x' || value[1] == 'X')) {
            base = 16;
            offset = 2;
        } else if (value.size() > 1 && value[0] == '0') {
            base = 8;
            offset = 1;
        }
    }
    if (base < 2 || base > 16 || offset == value.size()) {
        throw std::invalid_argument("invalid integer base or empty digit sequence");
    }

    uint64_t result{0};
    for (; offset < value.size(); ++offset) {
        const char c = value[offset];
        unsigned int digit;
        if (c >= '0' && c <= '9') digit = static_cast<unsigned int>(c - '0');
        else if (c >= 'a' && c <= 'f') digit = static_cast<unsigned int>(c - 'a') + 10;
        else if (c >= 'A' && c <= 'F') digit = static_cast<unsigned int>(c - 'A') + 10;
        else throw std::invalid_argument("integer contains an invalid digit");
        if (digit >= static_cast<unsigned int>(base) ||
            result > (UINT64_MAX - digit) / static_cast<unsigned int>(base)) {
            throw std::out_of_range("integer is outside the supported range");
        }
        result = result * static_cast<unsigned int>(base) + digit;
    }
    return result;
}

std::string Hex(const unsigned char* data, size_t size)
{
    std::ostringstream out;
    out << std::hex << std::setfill('0');
    for (size_t i = 0; i < size; ++i) out << std::setw(2) << unsigned(data[i]);
    return out.str();
}

bool DecodeCompact(uint32_t bits, Bytes32& target)
{
    const unsigned int size = bits >> 24;
    uint32_t word = bits & 0x007fffff;
    const bool negative = word != 0 && (bits & 0x00800000);
    const bool overflow = word != 0 &&
        (size > 34 || (word > 0xff && size > 33) || (word > 0xffff && size > 32));
    if (negative || overflow || word == 0) return false;

    // Decode the 3-byte mantissa into a 256-bit big-endian target. The
    // overflow checks above intentionally preserve Bitcoin Core's compact
    // encoding rules, including valid size-33/34 values with leading zeros.
    const int shift_bytes = size <= 3 ? 0 : static_cast<int>(size) - 3;
    if (size <= 3) word >>= 8 * (3 - size);
    target.fill(0);
    for (int i = 0; i < 3; ++i) {
        const unsigned char byte = static_cast<unsigned char>(word >> (8 * i));
        if (byte == 0) continue;
        const int position = 31 - shift_bytes - i;
        if (position < 0 || position >= 32) return false;
        target[position] = byte;
    }
    return std::any_of(target.begin(), target.end(), [](unsigned char b) { return b != 0; });
}

bool LessOrEqual(const Bytes32& a, const Bytes32& b)
{
    return !std::lexicographical_compare(b.begin(), b.end(), a.begin(), a.end());
}

HeaderPrefix MakePrefix(const Bytes32& merkle_display, uint32_t timestamp, uint32_t bits)
{
    HeaderPrefix prefix{};
    prefix[0] = 1; // nVersion = 1, little-endian
    for (size_t i = 0; i < 32; ++i) prefix[36 + i] = merkle_display[31 - i];
    for (unsigned int i = 0; i < 4; ++i) {
        prefix[68 + i] = static_cast<unsigned char>(timestamp >> (8 * i));
        prefix[72 + i] = static_cast<unsigned char>(bits >> (8 * i));
    }
    return prefix;
}

void HashHeader(const SHA256_CTX& first_block_state, const HeaderPrefix& prefix,
                uint32_t nonce, Bytes32& digest)
{
    unsigned char tail[16];
    std::memcpy(tail, prefix.data() + 64, 12);
    for (unsigned int i = 0; i < 4; ++i) tail[12 + i] = static_cast<unsigned char>(nonce >> (8 * i));

    SHA256_CTX ctx = first_block_state;
    unsigned char first_hash[SHA256_DIGEST_LENGTH];
    if (SHA256_Update(&ctx, tail, sizeof(tail)) != 1 ||
        SHA256_Final(first_hash, &ctx) != 1 ||
        SHA256(first_hash, sizeof(first_hash), digest.data()) == nullptr) {
        throw std::runtime_error("OpenSSL SHA-256 operation failed");
    }
}

bool SelfTest()
{
    if (ParseUnsigned("4294967295") != 0xffffffffULL ||
        ParseUnsigned("0x1d00ffff", 0) != 0x1d00ffffULL) return false;
    for (const char* invalid : {"", "-1", "12x", "1.0"}) {
        try {
            (void)ParseUnsigned(invalid);
            return false;
        } catch (const std::invalid_argument&) {
        }
    }

    // Bitcoin genesis header is a public SHA-256d serialization test vector.
    const Bytes32 merkle = ParseHex32("4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b");
    const Bytes32 approved_pow_limit = ParseHex32("00000000ffffffffffffffffffffffffffffffffffffffffffffffffffffffff");
    const Bytes32 genesis_compact_target = ParseHex32(
        "00000000ffff0000000000000000000000000000000000000000000000000000");
    Bytes32 decoded_target{};
    if (!DecodeCompact(0x1d00ffff, decoded_target) || decoded_target != genesis_compact_target ||
        !LessOrEqual(decoded_target, approved_pow_limit)) return false;
    if (DecodeCompact(0x1d80ffff, decoded_target) ||
        DecodeCompact(0x01000000, decoded_target) ||
        DecodeCompact(0x23000001, decoded_target)) return false;
    if (!DecodeCompact(0x2100ffff, decoded_target) ||
        Hex(decoded_target.data(), decoded_target.size()) != "ffff" + std::string(60, '0')) return false;
    if (!DecodeCompact(0x220000ff, decoded_target) ||
        Hex(decoded_target.data(), decoded_target.size()) != "ff" + std::string(62, '0')) return false;
    const auto prefix = MakePrefix(merkle, 1231006505, 0x1d00ffff);
    SHA256_CTX base{};
    if (SHA256_Init(&base) != 1 || SHA256_Update(&base, prefix.data(), 64) != 1) return false;
    Bytes32 digest{};
    HashHeader(base, prefix, 2083236893, digest);
    Bytes32 display{};
    std::reverse_copy(digest.begin(), digest.end(), display.begin());
    return Hex(display.data(), display.size()) ==
        "000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f";
}

struct SearchResult {
    bool found{false};
    uint32_t nonce{0};
    Bytes32 hash_display{};
};

int Search(const HeaderPrefix& prefix, const Bytes32& target, uint64_t start_nonce,
           uint64_t max_hashes, unsigned int thread_count)
{
    SHA256_CTX base{};
    if (SHA256_Init(&base) != 1 || SHA256_Update(&base, prefix.data(), 64) != 1) {
        throw std::runtime_error("could not initialize SHA-256 context");
    }

    const uint64_t available = NONCE_LIMIT - start_nonce;
    const uint64_t search_count = max_hashes == 0 ? available : std::min(max_hashes, available);
    const uint64_t end_nonce = start_nonce + search_count;
    std::atomic<uint64_t> next{start_nonce};
    std::atomic<uint64_t> completed_hashes{0};
    std::atomic<uint64_t> next_progress_report{10'000'000};
    std::atomic<bool> stop{false};
    const auto search_started = std::chrono::steady_clock::now();
    SearchResult result;
    std::mutex result_mutex;
    constexpr uint64_t CHUNK = 4096;

    std::vector<std::thread> workers;
    workers.reserve(thread_count);
    for (unsigned int worker = 0; worker < thread_count; ++worker) {
        workers.emplace_back([&] {
            while (!stop.load(std::memory_order_relaxed)) {
                const uint64_t begin = next.fetch_add(CHUNK, std::memory_order_relaxed);
                if (begin >= end_nonce) break;
                const uint64_t end = std::min(begin + CHUNK, end_nonce);
                uint64_t chunk_hashes{0};
                for (uint64_t n = begin; n < end && !stop.load(std::memory_order_relaxed); ++n) {
                    ++chunk_hashes;
                    Bytes32 digest{};
                    HashHeader(base, prefix, static_cast<uint32_t>(n), digest);
                    Bytes32 display{};
                    std::reverse_copy(digest.begin(), digest.end(), display.begin());
                    if (LessOrEqual(display, target)) {
                        std::lock_guard<std::mutex> lock(result_mutex);
                        if (!result.found) {
                            result.found = true;
                            result.nonce = static_cast<uint32_t>(n);
                            result.hash_display = display;
                            stop.store(true, std::memory_order_relaxed);
                        }
                        break;
                    }
                }
                const uint64_t total = completed_hashes.fetch_add(
                    chunk_hashes, std::memory_order_relaxed) + chunk_hashes;
                uint64_t threshold = next_progress_report.load(std::memory_order_relaxed);
                while (total >= threshold) {
                    if (next_progress_report.compare_exchange_weak(
                            threshold, threshold + 10'000'000, std::memory_order_relaxed)) {
                        const double seconds = std::chrono::duration<double>(
                            std::chrono::steady_clock::now() - search_started).count();
                        const double rate = seconds > 0 ? total / seconds : 0;
                        std::cerr << "{\"status\":\"search_progress\",\"hashes_tested\":"
                                  << total << ",\"hashes_per_second\":" << static_cast<uint64_t>(rate)
                                  << "}\n";
                        break;
                    }
                }
            }
        });
    }
    for (auto& worker : workers) worker.join();

    if (!result.found) {
        std::cout << "{\"status\":\"not_found\",\"start_nonce\":" << start_nonce
                  << ",\"searched_until_exclusive\":" << end_nonce << "}\n";
        return 2;
    }

    std::array<unsigned char, 80> header{};
    std::copy(prefix.begin(), prefix.end(), header.begin());
    for (unsigned int i = 0; i < 4; ++i) header[76 + i] = static_cast<unsigned char>(result.nonce >> (8 * i));

    // Independently hash the completed 80-byte header from a fresh SHA context.
    unsigned char first[SHA256_DIGEST_LENGTH];
    Bytes32 verify{};
    if (SHA256(header.data(), header.size(), first) == nullptr ||
        SHA256(first, sizeof(first), verify.data()) == nullptr) {
        throw std::runtime_error("final proof-of-work verification failed to hash");
    }
    Bytes32 verify_display{};
    std::reverse_copy(verify.begin(), verify.end(), verify_display.begin());
    if (verify_display != result.hash_display || !LessOrEqual(verify_display, target)) {
        throw std::runtime_error("found nonce failed independent full-header proof-of-work verification");
    }

    std::cout << "{\"status\":\"nonce_found_and_verified\",\"nonce\":" << result.nonce
              << ",\"block_hash\":\"" << Hex(result.hash_display.data(), 32)
              << "\",\"header_hex\":\"" << Hex(header.data(), header.size()) << "\"}\n";
    return 0;
}

} // namespace

int main(int argc, char** argv)
{
    try {
        if (argc == 2 && std::string(argv[1]) == "--self-test") {
            if (!SelfTest()) {
                std::cerr << "SHA-256d self-test failed\n";
                return 1;
            }
            std::cout << "SHA-256d header self-test passed\n";
            return 0;
        }

        std::string merkle_hex, pow_limit_hex;
        uint64_t timestamp = 0, bits_value = 0, start_nonce = 0, max_hashes = 0;
        bool timestamp_set{false};
        bool bits_set{false};
        uint64_t threads_value = std::max(1u, std::thread::hardware_concurrency());
        for (int i = 1; i < argc; ++i) {
            const std::string arg = argv[i];
            auto value = [&]() -> std::string {
                if (++i >= argc) throw std::invalid_argument("missing value for " + arg);
                return argv[i];
            };
            if (arg == "--merkle-root") merkle_hex = value();
            else if (arg == "--pow-limit") pow_limit_hex = value();
            else if (arg == "--time") {
                timestamp = ParseUnsigned(value());
                timestamp_set = true;
            }
            else if (arg == "--n-bits") {
                bits_value = ParseUnsigned(value(), 0);
                bits_set = true;
            }
            else if (arg == "--start-nonce") start_nonce = ParseUnsigned(value());
            else if (arg == "--max-hashes") max_hashes = ParseUnsigned(value());
            else if (arg == "--threads") threads_value = ParseUnsigned(value());
            else throw std::invalid_argument("unknown argument: " + arg);
        }

        if (merkle_hex.empty() || pow_limit_hex.empty() || !timestamp_set || !bits_set) {
            throw std::invalid_argument("--merkle-root, --time, --n-bits and --pow-limit are required");
        }
        if (timestamp > 0xffffffffULL || bits_value > 0xffffffffULL ||
            start_nonce > 0xffffffffULL || threads_value == 0 || threads_value > 256) {
            throw std::invalid_argument("time, nBits and start nonce must fit uint32; threads must be between 1 and 256");
        }
        const auto merkle = ParseHex32(merkle_hex);
        const auto pow_limit = ParseHex32(pow_limit_hex);
        Bytes32 target{};
        if (!DecodeCompact(static_cast<uint32_t>(bits_value), target)) {
            throw std::invalid_argument("nBits is negative, zero, overflowing, or exceeds 256 bits");
        }
        if (std::lexicographical_compare(pow_limit.begin(), pow_limit.end(), target.begin(), target.end())) {
            throw std::invalid_argument("decoded nBits target exceeds the approved powLimit");
        }
        const auto prefix = MakePrefix(merkle, static_cast<uint32_t>(timestamp), static_cast<uint32_t>(bits_value));
        return Search(prefix, target, start_nonce, max_hashes, static_cast<unsigned int>(threads_value));
    } catch (const std::exception& e) {
        std::cerr << "error: " << e.what() << '\n';
        return 1;
    }
}
