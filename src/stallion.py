import numpy as np

class Stallion:
    def __init__(self, video_bit_rate, window_size=8, z_thr=0.3, z_latency=0.75):
        """
        :param video_bit_rate: Lista de bitrates disponíveis (em Kbps).
        :param window_size: Tamanho da janela deslizante para métricas.
        :param z_thr: Fator de sensibilidade ao desvio padrão do throughput.
        :param z_latency: Fator de sensibilidade à latência (opcional).
        """
        self.video_bit_rate = video_bit_rate
        self.window_size = window_size
        self.z_thr = z_thr
        self.z_latency = z_latency

        # Atributos internos
        self.last_quality = 1
        self.thr_window = []
        self.lat_window = []

    def update_metrics(self, throughput_kbps, latency_s):
        """
        :param throughput_kbps: throughput atual em Kbps.
        :param latency_s: latência atual em segundos.
        """
        # Controle de janela
        if len(self.thr_window) >= self.window_size:
            self.thr_window.pop(0)
        if len(self.lat_window) >= self.window_size:
            self.lat_window.pop(0)

        self.thr_window.append(throughput_kbps)
        self.lat_window.append(latency_s)

    def select_quality(self):
        """
        Retorna o índice da qualidade (0..len(video_bit_rate)-1).
        """
        if not self.thr_window:
            return self.last_quality  # sem dados, mantém

        avg_thr = np.mean(self.thr_window)
        std_thr = np.std(self.thr_window)
 
        # Throughput seguro (Kbps)
        safe_thr = avg_thr - self.z_thr * std_thr
        if safe_thr < 0:
            safe_thr = 0.0

        # (Opcional) penalizar latência
        avg_lat = np.mean(self.lat_window)
        std_lat = np.std(self.lat_window)
        safe_lat = avg_lat + self.z_latency * std_lat

        # Exemplo: se latência acima de 1.0s, penaliza throughput
        LAT_THRESHOLD = 4
        if safe_lat > LAT_THRESHOLD:
            factor = safe_lat / LAT_THRESHOLD
            safe_thr /= factor  # reduz safe_thr

        # Agora escolhemos o maior bitrate <= safe_thr
        chosen_quality = 0
        for i in reversed(range(len(self.video_bit_rate))):
            if self.video_bit_rate[i] <= safe_thr:
                chosen_quality = i
                break

        # print(f"thr={avg_thr:.2f} std={std_thr:.2f} safe_thr={safe_thr:.2f} "
        #       f"lat={avg_lat:.2f} std={std_lat:.2f} safe_lat={safe_lat:.2f} "
        #       f"quality={chosen_quality}")
        self.last_quality = chosen_quality

        return self.last_quality
