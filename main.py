# Dieses Programm implementiert eine GUI-Anwendung zur Steuerung eines mobilen Roboters über Bluetooth.
# Die GUI besteht aus zwei Seiten:
# 1. Seite 1 (Page1): 
#    - Zeigt eine Liste der verfügbaren Bluetooth-Geräte an.
#    - Ermöglicht die Verbindung zu einem Gerät.
#    - Enthält einen Button, um zur Steuerungsseite (Seite 2) zu wechseln.
# 2. Seite 2 (Page2): 
#    - Ermöglicht die Steuerung des Roboters, einschließlich:
#      - Starten und Stoppen des Roboters.
#      - Anpassen der Geschwindigkeit der Motoren über Schieberegler.
#      - Ein- und Ausschalten der LED.
# Die Anwendung verwendet die Kivy-Bibliothek für die GUI und Bleak für die Bluetooth-Kommunikation.

import kivy
import threading
import asyncio
from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
import json
from bleak import BleakScanner, BleakClient
from kivy.core.window import Window
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen

class Page1(Screen):
    def go_to_page2(self):
        # Wechselt zu Seite 2.
        self.manager.current = 'page2'

class Page2(Screen):
    def go_to_page1(self):
        # Wechselt zu Seite 1.
        self.manager.current = 'page1'

class MyApp(App):
    def __init__(self, **kwargs):
        # Initialisiert die Anwendung.
        super().__init__(**kwargs)
        self.is_connected = False
        self.client = None
        self.selected_address = None
        self.ESP32_ADDRESS = "08:F9:E0:F4:8B:62"
        self.CHARACTERISTIC_UUID = "19b10001-e8f2-537e-4f6c-d104768a1214"
    
    def build(self):
        # Erstellt die Benutzeroberfläche der Anwendung.
        self.title = "Bluetooth Robotersteuerung"
        Window.size = (300, 600)
        Window.left = 500
        Window.top = 50
        Builder.load_file('main.kv')
        sm = ScreenManager()
        sm.add_widget(Page1(name='page1'))
        sm.add_widget(Page2(name='page2'))
        return sm

    def connect_to_device(self):
        # Startet einen Thread, um eine Verbindung zum ausgewählten Bluetooth-Gerät herzustellen.
        threading.Thread(target=self.connect_to_device_thread).start()

    def connect_to_device_thread(self):
        # Führt die asynchrone Verbindungslogik in einem separaten Thread aus.
        asyncio.run(self.connect_to_device_async())

    async def connect_to_device_async(self):
        # Stellt asynchron eine Verbindung zum ausgewählten Bluetooth-Gerät her.
        try:
            self.is_connected = True          
            async with BleakClient(self.selected_address) as client:
                self.client = client
                self.update_device_status(self.selected_address, "Verbunden")
                while self.is_connected:
                    if not client.is_connected:
                        self.is_connected = False
                        break
        except Exception as e:
            print(f"Fehler: {e}")

    async def _scan_devices(self):
        # Scannt nach verfügbaren Bluetooth-Geräten und aktualisiert die Geräteliste.
        try:
            # Geräte scannen
            devices = await BleakScanner.discover()
            print("Gefundene Geräte:")
            for device in devices:
                print(f"Name: {device.name}, Adresse: {device.address}")

            # Filtere Geräte, die mit "MOBIL_ROBOT" beginnen
            filtered_devices = [device for device in devices if device.name and device.name.startswith("MOBIL_ROBOT")]

            if filtered_devices:
                # Wähle das erste passende Gerät aus
                selected_device = filtered_devices[0]
                print(f"Passendes Gerät gefunden: {selected_device.name}, Adresse: {selected_device.address}")
                self.selected_address = selected_device.address  # Speichere die Adresse
            else:
                # Kein passendes Gerät gefunden, Standardadresse verwenden
                print("Kein passendes Gerät gefunden, Standardadresse verwenden.")
                self.selected_address = self.ESP32_ADDRESS
            
            device_names = [device.name if device.name else "Unbekanntes Gerät" for device in devices]
            Clock.schedule_once(lambda dt: self.update_device_list(device_names))

        except Exception as e:
            print(f"Fehler beim Scannen der Geräte: {e}")
            self.selected_address = self.ESP32_ADDRESS  # Fallback auf Standardadresse

    def update_device_list(self, device_names):
        # Aktualisiert die Benutzeroberfläche mit der Liste der verfügbaren Bluetooth-Geräte.
        filtered_device_names = [name for name in device_names if name and name.startswith("MOBIL_ROBOT")]
        device_list_container = self.root.get_screen('page1').ids.device_list
        
        for name in filtered_device_names:
            device_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)

            # Bluetooth-Symbol
            blu_icon = Image(source='bluetooth_icon.png', size_hint=(None, None), size=(40, 40))
            device_layout.add_widget(blu_icon)

            # Label für Gerätenamen
            device_label = Label(text=name, size_hint_x=0.6)
            device_layout.add_widget(device_label)

            # "Connect"-Button
            connect_btn = Button(text="Connect", size_hint_x=0.3)
            connect_btn.bind(on_press=lambda x: App.get_running_app().on_device_selected(name))
            device_layout.add_widget(connect_btn)

            # Gerätelayout zur Geräte-Liste hinzufügen
            device_list_container.add_widget(device_layout)

    def start_scan_devices(self):
        # Startet das Scannen nach Bluetooth-Geräten in einem separaten Thread.
        threading.Thread(target=self.scan_devices_thread).start()

    def scan_devices_thread(self):
        # Führt die asynchrone Gerätescan-Logik in einem separaten Thread aus.
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._scan_devices())

    def on_device_selected(self, device_name):
        # Behandelt die Auswahl eines Bluetooth-Geräts.
        device_list_container = self.root.get_screen('page1').ids.device_list
        roboter_button = self.root.get_screen('page1').ids.roboter_button

        for child in device_list_container.children:
            if isinstance(child, BoxLayout):
                connect_btn = child.children[0]
                if isinstance(connect_btn, Button):
                    if connect_btn.text == "Connect" and child.children[1].text == device_name:
                        connect_btn.text = "Disconnect"
                        self.connect_to_device()
                        if roboter_button:
                            print("roboter_button")
                        roboter_button.disabled = False
                    elif connect_btn.text == "Disconnect" and child.children[1].text == device_name:
                        connect_btn.text = "Connect"
                        self.stop_connection()
                        roboter_button.disabled = True

    def update_device_status(self, device_name, status):
        # Aktualisiert den Verbindungsstatus eines Bluetooth-Geräts.
        print(f"{device_name} - {status}")

    def stop_connection(self):
        # Beendet die Verbindung zum Bluetooth-Gerät.
        self.is_connected = False  

    async def send_data(self, data):
        # Sendet Daten an das verbundene Bluetooth-Gerät.
        if self.client and self.client.is_connected:
            json_data = json.dumps(data)
            await self.client.write_gatt_char(self.CHARACTERISTIC_UUID, json_data.encode("utf-8"))
            print("Daten gesendet:", data)
        else:
            print("Kein Gerät verbunden oder Verbindung nicht aktiv.")

    def set_mode(self, instance):
        # Setzt den Modus des Roboters und setzt die Schieberegler zurück.
        slider1 = self.root.get_screen('page2').ids.slider1
        slider2 = self.root.get_screen('page2').ids.slider2

        if instance.text == "stop":
            slider1.value = 0
            slider2.value = 0
        else:
            slider1.value = 50
            slider2.value = 50

        print("set_mode aufrufen")
        asyncio.run(self._set_mode_async(instance))
               
    async def _set_mode_async(self, instance):
        # Setzt den Modus des Roboters asynchron.

        print("_set_mode_async aurfuen")
        print(instance.text)
        if instance.text == "stop":
            instance.text = "start"
          
            await self.send_data({"ma": 0, "mb": 0})  # Warten, bis die Daten gesendet wurden
            #await self.send_data({"mode": "stop"})  
        elif instance.text == "start":
            instance.text = "stop"
            await self.send_data({"ma": 50, "mb": 50})  # Warten, bis die Daten gesendet wurden
            #await self.send_data({"mode": "start"})  

    def spliter_update_data(self, slider_name, value):
        # Aktualisiert die Motorgeschwindigkeit basierend auf Änderungen der Schieberegler.
        print(f"Slider {slider_name} mit Wert {value} wurde geändert")

        # Runden der Werte auf 2 Dezimalstellen
        rounded_value = round(value)
        
        # Bestimme, welcher Motor gesteuert wird und behalte den Wert des anderen Motors bei
        if slider_name == 'slider1':
            data = {"ma": rounded_value}  # Motor A Steuerung, Motor B bleibt unverändert
        elif slider_name == 'slider2':
            data = {"mb": rounded_value}  # Motor B Steuerung, Motor A bleibt unverändert

        asyncio.run(self.send_data(data))


    def power_led(self, instance, active):
        # Schaltet die LED basierend auf dem Zustand des Schalters ein oder aus.
        if active:
            data = {"led": 1}
        else:
            data = {"led": 0}
        
        asyncio.run(self.send_data(data))

if __name__ == '__main__':
    MyApp().run()
