import os
import psutil
import subprocess
import time

def get_cpu_temperature():
    try:
        output = subprocess.check_output(['sensors'], encoding='utf-8')
        for line in output.split('\n'):
            if line.strip().startswith('Tctl:'):
                temp_str = line.split('+')[1].split('°')[0]
                return float(temp_str)
    except (FileNotFoundError, subprocess.CalledProcessError, IndexError):
        return None
    return None

def get_gpu_stats():
    try:
        output = subprocess.check_output(['sensors'], encoding='utf-8')
        temp = None
        fan = None
        in_amdgpu_section = False
        for line in output.split('\n'):
            if 'amdgpu-pci' in line:
                in_amdgpu_section = True
            if in_amdgpu_section:
                if line.strip().startswith('edge:'):
                    temp_str = line.split('+')[1].split('°')[0]
                    temp = float(temp_str)
                if line.strip().startswith('fan1:'):
                    fan_str = line.split()[1]
                    fan = int(fan_str)
                    if temp is not None:
                        break
        return temp, fan
    except (FileNotFoundError, subprocess.CalledProcessError, IndexError):
        return None, None

def get_ram_utilization():
    return psutil.virtual_memory().percent

def get_network_bandwidth():
    net_io = psutil.net_io_counters()
    return net_io.bytes_sent, net_io.bytes_recv

def create_bar_graph(value, max_value, length=20):
    if value is None:
        return "[ N/A ]"
    if max_value == 0:
        return "[ N/A ]"
    
    value = min(value, max_value)

    bar_length = int((value / max_value) * length)
    bar = '#' * bar_length + '─' * (length - bar_length)
    return f"[{bar}] {value:.2f}"

def format_speed(speed_bytes_per_sec):
    speed_kb_per_sec = speed_bytes_per_sec / 1024
    if speed_kb_per_sec >= 1024:
        speed_mb_per_sec = speed_kb_per_sec / 1024
        return f"{speed_mb_per_sec:.2f} MB/s"
    else:
        return f"{speed_kb_per_sec:.2f} KB/s"

def main():
    last_net_io = get_network_bandwidth()
    if last_net_io is None:
        last_net_io = (0, 0)

    while True:
        try:
            output_lines = []
            output_lines.append("--- Shell Stats ---")

            # CPU Temp
            cpu_temp = get_cpu_temperature()
            output_lines.append(f"CPU Temp:  {create_bar_graph(cpu_temp, 100)}°C")

            # GPU Stats
            gpu_temp, gpu_fan = get_gpu_stats()
            output_lines.append(f"GPU Temp:  {create_bar_graph(gpu_temp, 110)}°C")
            output_lines.append(f"GPU Fan:   {create_bar_graph(gpu_fan, 3300, 20)} RPM")

            # RAM Utilization
            ram_percent = get_ram_utilization()
            output_lines.append(f"RAM Usage: {create_bar_graph(ram_percent, 100)}%")

            # Network Bandwidth
            current_net_io = get_network_bandwidth()
            if current_net_io and last_net_io:
                bytes_sent = current_net_io[0] - last_net_io[0]
                bytes_recv = current_net_io[1] - last_net_io[1]
                last_net_io = current_net_io
            else:
                bytes_sent, bytes_recv = 0, 0

            output_lines.append(f"Upload:    {format_speed(bytes_sent)}")
            output_lines.append(f"Download:  {format_speed(bytes_recv)}")
            
            output_lines.append("\nPress Ctrl+C to exit.")

            # Clear screen and print the entire buffer at once
            print("\033[H\033[J" + "\n".join(output_lines), end="")

            time.sleep(1)
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            break

if __name__ == "__main__":
    main()

