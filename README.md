# Step 1: INSTALL DEBIAN BULLSEYE
Other distributions often do not work.
- Download the image from the [Raspberry Pi website](https://www.raspberrypi.org/software/operating-systems/).
- Alternatively, use the [Raspberry Pi Imager](https://www.raspberrypi.com/software/).
#### Headless Setup (optional):
- If using 'Raspberry Pi OS Lite', connect a keyboard and monitor for the first boot.
- Create an empty `ssh` file inside the `/boot` directory to enable SSH access.
- Alternatively, configure SSH and user credentials using the Raspberry Pi Imager before flashing.


# Step 2: VLAN Configuration
## Enable VLAN Support
```bash
modprobe 8021q
echo 8021 >> /etc/modules
```
Restart the networking services to apply the changes:
```bash
sudo systemctl restart dhcpcd
sudo systemctl restart networking
```

## Example Configuration To connect to the Lab Vlan
### `/etc/dhcpcd.conf`:
```plaintext
interface eth0.204
static ip_address=10.1.6.XXX/24
static routers=10.1.6.1
static domain_name_servers=8.8.8.8
```

#### `/etc/network/interfaces`:
```plaintext
auto eth0.204
iface eth0.204 inet manual
vlan-raw-device eth0
```

# Step 3: Steps to Set Up Raspberry Pi OS

## Open a Terminal
- On the desktop version, open a terminal window.
- On the headless version, connect via SSH with your configured user and password.

## Configure Serial Port
Run the `raspi-config` tool:
```bash
sudo raspi-config
```
- **Disable login shell over serial:**
  - Navigate to `Interface Options > Serial Port`.
  - Select `No` when asked if you want the login shell accessible over serial.
    
  ![001_login_shell_question](https://github.com/user-attachments/assets/9c55a7ac-a641-4872-8f53-37b1adadc124)

  - Select `Yes` to enable the serial port hardware.
    
  ![002_serial_enable](https://github.com/user-attachments/assets/e4297412-907c-4d4c-916c-0def398a703f)

  - Confirm and return to the main menu.
- Exit and select **No** when prompted to reboot.


## Disable Bluetooth
Edit the `/boot/config.txt` file:
```bash
sudo nano /boot/config.txt
```
Add the following line at the end:
```plaintext
dtoverlay=disable-bt
```
For Raspberry Pi 5, also add:
```plaintext
dtoverlay=uart0
```
Save and exit. *(Note: If Bluetooth is required, skip this step and use `ttyS0` instead of `ttyAMA0`.)*

## Disable `hciuart` (Optional)
```bash
sudo systemctl disable hciuart
```

## Reboot
Reboot the system:
```bash
sudo reboot
```
Reconnect via SSH once the system is up.

---
# Step 4: Install Python and Utilities
1. Install `python3-serial`:
   ```bash
   sudo apt-get install python3-serial
   ```
2. Download and install the RPICT package:
   ```bash
   wget lechacal.com/RPICT/tools/lcl-rpict-package_latest.deb
   sudo dpkg -i lcl-rpict-package_latest.deb
   ```

3. Install Prometheus-client for later 
```bash
 pip install prometheus-client
```
---

# Step 5: Testing the Serial Port
**DO NOT SKIP THIS TEST.**
1. Insert the RPICT board.
2. Configure and read from the serial port:
   ```bash
   stty -echo -F /dev/ttyAMA0 raw speed 38400
   cat /dev/ttyAMA0
   ```
3. Alternatively, use:
   ```bash
   lcl-run
   ```
   Example output will display on the terminal.
   
![Screenshot_2021-03-12_21-27-04](https://github.com/user-attachments/assets/a23e7692-affb-417e-8bbc-9c7d39a24c10)


---

# Step 6: Updating RPICT Configurations via Web Interface
1. Start the web server:
   ```bash
   lcl-server.sh
   ```
2. Access the interface at:
   [http://raspberrypi:8000](http://raspberrypi:8000)
3. Load, modify, and send configurations as needed.
- Click on the button with the 'upload' icon, which has a hover tip saying "Load from Device."
This action will load all the current configurations from the device to the web interface.
4. Modify Configurations:
- Adjust the necessary configurations, such as changing the "number of slaves" or "output fields."
5. Send Configuration to the Device:
- Click on the button with the 'download' icon, which has a hover tip saying "Send to Device."
This action will push all the updated configurations from the web interface to your device.
6. Start Collecting Metrics:
- Click the "Start" button to begin collecting metrics based on the new configurations.
---

# Step 7:Updating the Arduino Sketch on RPICT
1. Check the current firmware version:
   ```bash
   lcl-show-header.py
   ```
2. Download the latest Arduino sketch:
   ```bash
   wget lechacal.com/RPICT/sketch/RPICT_MCP3208_v4.2.0.ino.hex
   ```
3. Install `avrdude`:
   ```bash
   sudo apt-get -y install avrdude
   ```
4. Upload the sketch:
   ```bash
   lcl-upload-sketch.sh RPICT_MCP3208_v4.2.0.ino.hex
   ```
   Last two lines of the output should look like this.
   
avrdude done.  Thank you.
strace: |autoreset: Tubería rota
   
6. Verify the installation:
   ```bash
   lcl-show-header.py
   ```

---

# Step 8: Make the code execute on boot 

Add a new .service file on the /system/ folder with: 
sudo nano /etc/systemd/system/EMON-client.service

Remember to also include the correct path to the .py code in ExecStart= and the WorkingDirectory= (where the json file is alocated) otherwise it won't load the directory and kill the process if JSON not load.

```bash
[Unit]
Description=Python Boot Script to start brodcasting EMON metrics to the server
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/cttc/Documentos/SensorResourceExporter/pythonCode.py
WorkingDirectory=/home/cttc/Documentos/SensorResourceExporter/
StandardOutput=journal
StandardError=journal
Restart=always
User=cttc
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
```

commit and check the service
```bash
sudo systemctl daemon-reload
sudo systemctl restart EMON-client.service
sudo systemctl status EMON-client.service
```
## Configuring a Static IP Address
1. Edit the network interface:
   ```plaintext
   enable
   configure terminal
   interface ce1
   ip address 192.168.10.1 255.255.255.0
   description "add information here"
   no shutdown
   write memory
   commit
   exit
   ```
2. Verify the static route:
   ```bash
   show ip route
   ```

---

## Energy Monitoring Using SNMP Exporter
1. Download and configure the SNMP exporter:
   ```bash
   wget https://github.com/prometheus/snmp_exporter/releases/latest
   sudo mkdir /etc/snmp_exporter
   sudo cp <downloaded_files> /etc/snmp_exporter/
   ```
2. Create the `snmp-exporter.service` file:
   ```plaintext
   [Unit]
   Description=SNMP Exporter
   Wants=network-online.target
   After=network-online.target

   [Service]
   ExecStart=/etc/snmp_exporter/snmp_exporter --config.file=/etc/snmp_exporter/snmp.yml
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
3. Start the service:
   ```bash
   sudo systemctl start snmp-exporter.service
   sudo systemctl status snmp-exporter.service
   ```

4. Configure Prometheus to collect metrics:
   ```plaintext
   - job_name: '<job_name>'
     static_configs:
       - targets:
         - 10.1.1.86
         - 10.1.1.87
     metrics_path: /snmp
     params:
       module: [if_mib]
     relabel_configs:
       - source_labels: [__address__]
         target_label: __param_target
       - source_labels: [__param_target]
         target_label: instance
       - target_label: __address__
         replacement: 10.1.1.88:9116
   ```
5. Restart Prometheus:
   ```bash
   sudo systemctl restart prometheus.service
   ```
``` 
