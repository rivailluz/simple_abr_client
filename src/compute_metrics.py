#!/usr/bin/env python3
import os
import csv
import matplotlib.pyplot as plt
import numpy as np

COMPARATIVE_GRAPHS_DIR = "/app/graphs/graphs_comparative"
BB_LOG_FOLDER = "/app/results/results_bb"
STALLION_LOG_FOLDER = "/app/results/results_stallion"

# Defina se deseja exportar o CSV consolidado:
EXPORT_CSV = True
CSV_OUTPUT_PATH = "/app/results/family_comparison.csv"

def compute_family_metrics(log_folder, algorithm_name):
    """
    Lê todos os arquivos de log em 'log_folder' (p.ex. BB ou Stallion)
    e agrupa as métricas por 'família' de trace.

    Inclui 'delays' para calcular latência média (ms).
    Retorna:
      family_dict[family_name] = {
          'bitrates': [],
          'total_stalls': [],
          'switches': [],
          'delays': []
      }
    """
    family_dict = {}
    log_files = [f for f in os.listdir(log_folder)
                if os.path.isfile(os.path.join(log_folder, f))]

    for log_file in log_files:
        log_path = os.path.join(log_folder, log_file)
        with open(log_path, "r") as f:
            reader = csv.reader(f)
            prev_bitrate = None
            total_stall = 0.0
            switches = 0
            bitrates = []
            delays = []
            for row in reader:
                # Esperamos 9 colunas:
                # [0]=alg, [1]=trace_name, [2]=time_stamp, [3]=bit_rate,
                # [4]=buffer_size, [5]=rebuf, [6]=chunk_size, [7]=delay, [8]=throughput
                if len(row) < 9:
                    continue
                try:
                    trace_name  = row[1].strip()
                    bit_rate    = float(row[3])   # kbps
                    rebuf       = float(row[5])   # s
                    delay_ms    = float(row[7])   # ms (interpretação de latência/download)
                except ValueError:
                    continue

                # Identifica a "família": ex. "norway_car_2" => "norway_car"
                parts = trace_name.rsplit("_", 1)
                if len(parts) == 2:
                    family_name = parts[0]
                else:
                    family_name = trace_name

                # Inicializa se não existe
                if family_name not in family_dict:
                    family_dict[family_name] = {
                        'bitrates': [],
                        'total_stalls': [],
                        'switches': [],
                        'delays': []
                    }

                # Atualiza valores
                bitrates.append(bit_rate)
                total_stall += rebuf
                delays.append(delay_ms)

                # Conta trocas de qualidade
                if prev_bitrate is None:
                    prev_bitrate = bit_rate
                else:
                    if bit_rate != prev_bitrate:
                        switches += 1
                    prev_bitrate = bit_rate

            # Após ler todo o log file, adiciona os valores agregados na família
            family_dict[family_name]['bitrates'].append(np.mean(bitrates) if bitrates else 0.0)
            family_dict[family_name]['total_stalls'].append(total_stall)
            family_dict[family_name]['switches'].append(switches)
            family_dict[family_name]['delays'].append(np.mean(delays) if delays else 0.0)

    return family_dict

def aggregate_family_dict(family_dict):
    """
    Mantém as listas de métricas por família.

    Retorna:
      result[family_name] = {
          'bitrates': [...],
          'total_stalls': [...],
          'switches': [...],
          'delays': [...]
      }
    """
    result = {}
    for family_name, data in family_dict.items():
        all_bitrates = data['bitrates']
        total_stalls = data['total_stalls']
        switches = data['switches']
        all_delays = data['delays']

        result[family_name] = {
            'bitrates': all_bitrates,
            'total_stalls': total_stalls,
            'switches': switches,
            'delays': all_delays
        }

    return result


# -------------------------
# FUNÇÕES DE PLOTAGEM COM BOXPLOTS
# -------------------------

def plot_family_separated_boxplots(family_name, bb_metrics, st_metrics):
    """
    Gera 4 boxplots SEPARADOS (bitrate, stalls, switches, latência)
    para a 'família' family_name, comparando BB vs. Stallion.
    """
    bb_bitrates = bb_metrics['bitrates']
    bb_stalls = bb_metrics['total_stalls']
    bb_switches = bb_metrics['switches']
    bb_delays = bb_metrics['delays']

    st_bitrates = st_metrics['bitrates']
    st_stalls = st_metrics['total_stalls']
    st_switches = st_metrics['switches']
    st_delays = st_metrics['delays']

    metrics = {
        'Bitrate (kbps)': (bb_bitrates, st_bitrates),
        'Total Stall (s)': (bb_stalls, st_stalls),
        'Switches': (bb_switches, st_switches),
        'Latency (ms)': (bb_delays, st_delays)
    }

    for metric_name, (bb_values, st_values) in metrics.items():
        plt.figure(figsize=(6, 4))
        data = [bb_values, st_values]
        plt.boxplot(data, labels=["BB", "Stallion"], patch_artist=True,
                    boxprops=dict(facecolor="lightblue"),
                    medianprops=dict(color="red"))
        plt.ylabel(metric_name)
        plt.title(f"[{family_name}] {metric_name}")
        out_png = os.path.join(COMPARATIVE_GRAPHS_DIR, f"{family_name}_{metric_name.replace(' ', '_')}.png")
        plt.savefig(out_png)
        plt.close()

def plot_family_all_in_one_boxplot(family_name, bb_metrics, st_metrics):
    """
    Gera UM gráfico com 4 boxplots agrupados: (Bitrate, Stall, Switches, Latency)
    comparando BB vs Stallion para essa 'família'.
    """
    bb_bitrates = bb_metrics['bitrates']
    bb_stalls = bb_metrics['total_stalls']
    bb_switches = bb_metrics['switches']
    bb_delays = bb_metrics['delays']

    st_bitrates = st_metrics['bitrates']
    st_stalls = st_metrics['total_stalls']
    st_switches = st_metrics['switches']
    st_delays = st_metrics['delays']

    metrics = {
        'Bitrate (kbps)': [bb_bitrates, st_bitrates],
        'Total Stall (s)': [bb_stalls, st_stalls],
        'Switches': [bb_switches, st_switches],
        'Latency (ms)': [bb_delays, st_delays]
    }

    labels = list(metrics.keys())
    data_bb = [metrics[label][0] for label in labels]
    data_st = [metrics[label][1] for label in labels]

    x = np.arange(len(labels))  # [0,1,2,3]
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))

    # Boxplots para BB
    box_bb = ax.boxplot(data_bb, positions=x - width/2, widths=width, patch_artist=True,
                       boxprops=dict(facecolor="lightblue"),
                       medianprops=dict(color="blue"))

    # Boxplots para Stallion
    box_st = ax.boxplot(data_st, positions=x + width/2, widths=width, patch_artist=True,
                       boxprops=dict(facecolor="lightcoral"),
                       medianprops=dict(color="red"))

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_ylabel("Valores")
    ax.set_title(f"Comparação Boxplots BB vs Stallion - Família: {family_name}")
    ax.legend([box_bb["boxes"][0], box_st["boxes"][0]], ["BB", "Stallion"])

    plt.tight_layout()
    out_png = os.path.join(COMPARATIVE_GRAPHS_DIR, f"compare_family_boxplot_{family_name}.png")
    plt.savefig(out_png)
    plt.close()


def plot_overall_boxplots(metric_label, bb_values, st_values):
    """
    Gera UM gráfico de boxplot comparando BB x Stallion
    para a soma ou média de todos os traces (Overall).
    """
    plt.figure(figsize=(6, 4))
    data = [bb_values, st_values]
    plt.boxplot(data, labels=["BB", "Stallion"], patch_artist=True,
                boxprops=dict(facecolor="lightblue"),
                medianprops=dict(color="red"))
    plt.ylabel(metric_label)
    plt.title(f"Comparação Geral - {metric_label}")
    out_png = os.path.join(COMPARATIVE_GRAPHS_DIR, f"overall_boxplot_{metric_label.replace(' ', '_')}.png")
    plt.savefig(out_png)
    plt.close()


def plot_big_unified_boxplots(all_families, bb_agg, st_agg):
    """
    Cria UM gráfico unificado (com 4 subplots) comparando TODAS as famílias
    para 4 métricas (Bitrate, Stall, Switches, Latência).

    Em cada subplot:
      - Eixo x = cada família
      - Boxplots BB vs Stallion
    """
    # Ordena as famílias
    families = sorted(all_families)

    metrics = ['bitrates', 'total_stalls', 'switches', 'delays']
    metric_labels = ['Bitrate (kbps)', 'Total Stall (s)', 'Switches', 'Latency (ms)']

    fig, axs = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle("Boxplots Comparativos: Todas as Famílias x 4 Métricas")

    for idx, (metric, label) in enumerate(zip(metrics, metric_labels)):
        row = idx // 2
        col = idx % 2
        data_bb = [bb_agg.get(fam, {}).get(metric, []) for fam in families]
        data_st = [st_agg.get(fam, {}).get(metric, []) for fam in families]

        # Combina os dados para BB e Stallion
        data = []
        labels_combined = []
        for fam_idx, fam in enumerate(families):
            data.append(bb_agg.get(fam, {}).get(metric, []))
            data.append(st_agg.get(fam, {}).get(metric, []))
            labels_combined.append(f"{fam} BB")
            labels_combined.append(f"{fam} Stallion")

        axs[row, col].boxplot(data, labels=labels_combined, patch_artist=True,
                             boxprops=dict(facecolor="lightblue"),
                             medianprops=dict(color="red"))
        axs[row, col].set_title(label)
        axs[row, col].tick_params(axis='x', rotation=90)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])  # Ajusta para deixar espaço para o título
    out_png = os.path.join(COMPARATIVE_GRAPHS_DIR, "all_families_unified_boxplots.png")
    plt.savefig(out_png)
    plt.close()


def main():
    # 1) Lê e agrega métricas para BB
    bb_families = compute_family_metrics(BB_LOG_FOLDER, "bb")
    bb_agg = aggregate_family_dict(bb_families)

    # 2) Lê e agrega métricas para Stallion
    st_families = compute_family_metrics(STALLION_LOG_FOLDER, "stallion")
    st_agg = aggregate_family_dict(st_families)

    # 3) Lista de todas as famílias
    all_families = sorted(set(bb_agg.keys()).union(st_agg.keys()))
    if not os.path.exists(COMPARATIVE_GRAPHS_DIR):
        os.makedirs(COMPARATIVE_GRAPHS_DIR)

    # Variáveis para "Overall" (usando listas para boxplots)
    overall_bb_bitrates = []
    overall_bb_stalls = []
    overall_bb_switches = []
    overall_bb_delays = []

    overall_st_bitrates = []
    overall_st_stalls = []
    overall_st_switches = []
    overall_st_delays = []

    # Preparar CSV
    csv_lines = []
    csv_lines.append("family_name,algorithm,avg_bitrate,avg_stall,total_switches,avg_latency")

    print("== Métricas por Família ==")
    for fam in all_families:
        # Dados por família
        bb_metrics = bb_agg.get(fam, {'bitrates': [], 'total_stalls': [], 'switches': [], 'delays': []})
        st_metrics = st_agg.get(fam, {'bitrates': [], 'total_stalls': [], 'switches': [], 'delays': []})

        # Gera gráficos por família (separados e boxplot unificado)
        plot_family_separated_boxplots(fam, bb_metrics, st_metrics)
        plot_family_all_in_one_boxplot(fam, bb_metrics, st_metrics)

        # Print no console
        avg_bitrate_bb = np.mean(bb_metrics['bitrates']) if bb_metrics['bitrates'] else 0.0
        avg_stall_bb = np.mean(bb_metrics['total_stalls']) if bb_metrics['total_stalls'] else 0.0
        total_switches_bb = np.sum(bb_metrics['switches']) if bb_metrics['switches'] else 0
        avg_delay_bb = np.mean(bb_metrics['delays']) if bb_metrics['delays'] else 0.0

        avg_bitrate_st = np.mean(st_metrics['bitrates']) if st_metrics['bitrates'] else 0.0
        avg_stall_st = np.mean(st_metrics['total_stalls']) if st_metrics['total_stalls'] else 0.0
        total_switches_st = np.sum(st_metrics['switches']) if st_metrics['switches'] else 0
        avg_delay_st = np.mean(st_metrics['delays']) if st_metrics['delays'] else 0.0

        print(f"\nFamília: {fam}")
        print(f"  BB -> Bitrate Médio={avg_bitrate_bb:.2f} kbps, Stall Médio={avg_stall_bb:.2f}s, "
              f"Trocas={total_switches_bb}, Latência Média={avg_delay_bb:.2f}ms")
        print(f"  Stallion -> Bitrate Médio={avg_bitrate_st:.2f} kbps, Stall Médio={avg_stall_st:.2f}s, "
              f"Trocas={total_switches_st}, Latência Média={avg_delay_st:.2f}ms")

        # Salva no CSV
        csv_lines.append(f"{fam},BB,{avg_bitrate_bb:.2f},{avg_stall_bb:.2f},{total_switches_bb},{avg_delay_bb:.2f}")
        csv_lines.append(f"{fam},Stallion,{avg_bitrate_st:.2f},{avg_stall_st:.2f},{total_switches_st},{avg_delay_st:.2f}")

        # Acumula para "Overall" (listas para boxplots)
        overall_bb_bitrates.extend(bb_metrics['bitrates'])
        overall_bb_stalls.extend(bb_metrics['total_stalls'])
        overall_bb_switches.extend(bb_metrics['switches'])
        overall_bb_delays.extend(bb_metrics['delays'])

        overall_st_bitrates.extend(st_metrics['bitrates'])
        overall_st_stalls.extend(st_metrics['total_stalls'])
        overall_st_switches.extend(st_metrics['switches'])
        overall_st_delays.extend(st_metrics['delays'])

    # Plota comparações gerais usando boxplots
    plot_overall_boxplots("Bitrate (kbps)", overall_bb_bitrates, overall_st_bitrates)
    plot_overall_boxplots("Total Stall (s)", overall_bb_stalls, overall_st_stalls)
    plot_overall_boxplots("Switches", overall_bb_switches, overall_st_switches)
    plot_overall_boxplots("Latency (ms)", overall_bb_delays, overall_st_delays)

    print("\n== Comparação Geral (agregado) ==")
    overall_avg_bitrate_bb = np.mean(overall_bb_bitrates) if overall_bb_bitrates else 0.0
    overall_avg_stall_bb = np.mean(overall_bb_stalls) if overall_bb_stalls else 0.0
    overall_total_switches_bb = np.sum(overall_bb_switches) if overall_bb_switches else 0
    overall_avg_delay_bb = np.mean(overall_bb_delays) if overall_bb_delays else 0.0

    overall_avg_bitrate_st = np.mean(overall_st_bitrates) if overall_st_bitrates else 0.0
    overall_avg_stall_st = np.mean(overall_st_stalls) if overall_st_stalls else 0.0
    overall_total_switches_st = np.sum(overall_st_switches) if overall_st_switches else 0
    overall_avg_delay_st = np.mean(overall_st_delays) if overall_st_delays else 0.0

    print(f"BB ->   Bitrate Médio={overall_avg_bitrate_bb:.2f} kbps, "
          f"Stall Médio={overall_avg_stall_bb:.2f}s, "
          f"Switches Total={overall_total_switches_bb}, "
          f"Latência Média={overall_avg_delay_bb:.2f}ms")
    print(f"Stallion -> Bitrate Médio={overall_avg_bitrate_st:.2f} kbps, "
          f"Stall Médio={overall_avg_stall_st:.2f}s, "
          f"Switches Total={overall_total_switches_st}, "
          f"Latência Média={overall_avg_delay_st:.2f}ms")

    # Salva no CSV
    if EXPORT_CSV:
        csv_out_dir = os.path.dirname(CSV_OUTPUT_PATH)
        if csv_out_dir and not os.path.exists(csv_out_dir):
            os.makedirs(csv_out_dir)
        with open(CSV_OUTPUT_PATH, "w") as fcsv:
            fcsv.write("\n".join(csv_lines))
        print(f"\n[OK] Arquivo CSV gerado em: {CSV_OUTPUT_PATH}")

    # Gera gráfico unificado com boxplots para todas as famílias
    plot_big_unified_boxplots(all_families, bb_agg, st_agg)

    print(f"\n[INFO] Gráficos salvos em: {COMPARATIVE_GRAPHS_DIR}")


if __name__ == "__main__":
    main()
