#!/usr/bin/env python3
import os
import numpy as np
import load_trace
from bb import bb_algo
from stallion import Stallion
import fixed_env as env

# Parâmetros gerais
VIDEO_BIT_RATE = [300, 750, 1200, 1850, 2850, 4300]  # kbps
M_IN_K = 1000.0
DEFAULT_QUALITY = 1
RANDOM_SEED = 42
BMIN = 4 # Parâmetro para o BB
BB_LOG_FOLDER = "/app/results/results_bb"
STALLION_LOG_FOLDER = "/app/results/results_stallion"
LOG_FILE = "/log_"
TEST_TRACES = "/app/traces/"

def run_algorithm(algorithm, all_cooked_time, all_cooked_bw, all_file_names, log_folder):
    print(f"Executando {algorithm} Algorithm")

    if not os.path.exists(log_folder):
        os.makedirs(log_folder)

    net_env = env.Environment(all_cooked_time=all_cooked_time, all_cooked_bw=all_cooked_bw)

    # Abre o primeiro arquivo de log
    log_path = log_folder + LOG_FILE + all_file_names[net_env.trace_idx]
    log_file = open(log_path, "w")

    time_stamp_ms = 0.0  # manteraemos internalmente em ms
    bit_rate = DEFAULT_QUALITY

    # Instancia Stallion, se for o caso
    if algorithm == "stallion":
        algo_instance = Stallion(
            video_bit_rate=VIDEO_BIT_RATE,
            # Ajuste de parâmetros para ser mais conservador:
            window_size=8,   # mesma WINDOW_SIZE do Env
            z_thr=0.1,       # sensibilidade menor => Stallion menos agressivo,
            z_latency=1.5
        )

    video_count = 0
    while True:
        (
            delay_ms,         # em ms
            sleep_ms,         # em ms
            buffer_size_s,    # em segundos
            rebuf_s,          # em segundos
            video_chunk_size, # em bytes
            next_video_chunk_sizes,
            end_of_video,
            video_chunk_remain,
            raw_throughput_bytes_s  # bytes/s
        ) = net_env.get_video_chunk(bit_rate)

        # Atualiza tempo total em ms
        time_stamp_ms += delay_ms
        time_stamp_ms += sleep_ms

        # Converte throughput para kbps
        throughput_kbps = (raw_throughput_bytes_s * 8) / 1000.0
        # Converte time_stamp para segundos ao salvar no log
        time_s = time_stamp_ms / 1000.0

        # Monta a linha do log
        # Formato (9 colunas):
        # algorithm, trace_name, time_stamp_s, bit_rate_kbps, buffer_s, rebuffer_s, chunk_size_bytes, delay_ms, throughput_kbps
        # Usaremos "all_file_names[net_env.trace_idx]" como "trace_name" (2ª coluna do CSV).
        line = (
            f"{algorithm},"
            f"{all_file_names[net_env.trace_idx]},"  # trace_name
            f"{time_s},"                             # time_stamp (s)
            f"{VIDEO_BIT_RATE[bit_rate]},"           # chosen bit_rate (kbps)
            f"{buffer_size_s},"
            f"{rebuf_s},"
            f"{video_chunk_size},"
            f"{delay_ms},"
            f"{throughput_kbps}\n"
        )
        log_file.write(line)
        log_file.flush()

        # Decisão do próximo bitrate
        if algorithm == "bb":
            # BB: decide baseado no buffer
            bit_rate = bb_algo(buffer_size_s, VIDEO_BIT_RATE, DEFAULT_QUALITY, M_IN_K, BMIN)
        elif algorithm == "stallion":
            latency_s = delay_ms / 1000.0
            algo_instance.update_metrics(throughput_kbps, latency_s)
            bit_rate = algo_instance.select_quality()

        if end_of_video:
            video_count += 1
            log_file.write("\n")
            log_file.close()

            bit_rate = DEFAULT_QUALITY

            # fim total dos traces?
            if net_env.trace_idx >= len(all_cooked_time):
                break
            if video_count >= len(all_file_names):
                break

            log_path = log_folder + LOG_FILE + all_file_names[net_env.trace_idx]
            log_file = open(log_path, "w")


def main():
    np.random.seed(RANDOM_SEED)
    all_cooked_time, all_cooked_bw, all_file_names = load_trace.load_trace(TEST_TRACES)

    run_algorithm("bb", all_cooked_time, all_cooked_bw, all_file_names, BB_LOG_FOLDER)
    run_algorithm("stallion", all_cooked_time, all_cooked_bw, all_file_names, STALLION_LOG_FOLDER)
    print("Execução concluída. Logs salvos em:", BB_LOG_FOLDER, "e", STALLION_LOG_FOLDER)

if __name__ == "__main__":
    main()
