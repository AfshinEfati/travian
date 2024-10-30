import requests
import re
import math
from tkinter import Tk, Label, Entry, Button, StringVar, filedialog, ttk, Text, Scrollbar
from tkinter import messagebox
import threading
import time

def log_message(terminal, message):
    terminal.config(state="normal")
    terminal.insert('end', message + "\n")
    terminal.config(state="disabled")
    terminal.yview('end')

def fetch_village_details(session, site_url, x, y, terminal):
    village_details_url = f'{site_url}/api/v1/ajax/viewTileDetails'
    payload = {'x': x, 'y': y}
    try:
        response = session.post(village_details_url, json=payload)
        response_data = response.json()
        if 'html' in response_data:
            html_content = response_data['html']
            tribe_match = re.search(r'<th>نژاد<\/th>\s*<td>(.*?)<\/td>', html_content)
            if tribe_match:
                log_message(terminal, f"Fetched tribe for village ({x}, {y})")
                return tribe_match.group(1).strip()
        return 'Unknown Tribe'
    except Exception as e:
        log_message(terminal, f"Failed to fetch village details for coordinates ({x}, {y}): {e}")
        return 'Unknown Tribe'

def fetch_map_data(session, site_url, x_origin, y_origin, radius, quadrant, progress_bar, terminal):
    map_data_url = f'{site_url}/api/v1/ajax/mapPositionData'
    headers = {
        'x-requested-with': 'XMLHttpRequest',
        'origin': site_url,
        'referer': f'{site_url}/karte.php',
    }
    villages_by_ally = {}
    no_ally_villages = []
    unique_villages = set()
    
    x_min = x_origin - radius
    y_min = y_origin - radius
    x_max = x_origin + radius
    y_max = y_origin + radius

    progress_bar.start()

    log_message(terminal, "Starting map data fetch...")

    for x in range(x_min, x_max + 1):
        for y in range(y_min, y_max + 1):
            if math.sqrt((x - x_origin) ** 2 + (y - y_origin) ** 2) > radius:
                continue
            if quadrant == 'NE' and (x < 0 or y < 0):
                continue
            elif quadrant == 'SE' and (x < 0 or y > 0):
                continue
            elif quadrant == 'NW' and (x > 0 or y < 0):
                continue
            elif quadrant == 'SW' and (x > 0 or y > 0):
                continue
            
            payload = {
                'data': {
                    'x': x,
                    'y': y,
                    'zoomLevel': 1,
                    'ignorePositions': []
                }
            }

            try:
                response = session.post(map_data_url, headers=headers, json=payload)
                response_data = response.json()

                if 'tiles' in response_data:
                    for tile in response_data['tiles']:
                        if tile.get('did') is None:
                            continue

                        tile_text = tile.get('text', '')
                        alliance_match = re.search(r'{k\.allianz}\s*(.*?)<br>', tile_text)
                        player_match = re.search(r'{k\.spieler}\s*(.*?)<br>', tile_text)

                        alliance = alliance_match.group(1).strip() if alliance_match else 'No Alliance'
                        player = player_match.group(1).strip() if player_match else 'Unknown Player'

                        if player == 'ناتار ها' or player == 'Unknown Player':
                            continue

                        x_coord = int(tile['position']['x'])
                        y_coord = int(tile['position']['y'])

                        village_position = (x_coord, y_coord)
                        if village_position in unique_villages:
                            continue  

                        unique_villages.add(village_position)

                        village_data = {
                            'coordinates': f"({x_coord}, {y_coord})",
                            'player': player,
                            'link': f"{site_url}/position_details.php?x={x_coord}&y={y_coord}"
                        }

                        log_message(terminal, f"Processed village at {village_data['coordinates']}")

                        if alliance != 'No Alliance':
                            if alliance not in villages_by_ally:
                                villages_by_ally[alliance] = []

                            villages_by_ally[alliance].append(village_data)
                        else:
                            no_ally_villages.append(village_data)

            except Exception as e:
                log_message(terminal, f"Failed to fetch data for coordinates ({x}, {y}): {e}")

    progress_bar.stop()
    log_message(terminal, "Finished fetching map data.")

    return unique_villages, villages_by_ally, no_ally_villages

def fetch_village_tribes(session, site_url, villages, terminal):
    village_details = {}

    for village in villages:
        x, y = village
        tribe = fetch_village_details(session, site_url, x, y, terminal)
        village_details[village] = tribe  

    return village_details

def generate_html_report(villages_by_ally, no_ally_villages, village_details):
    html_content = """
    <html>
    <head>
        <title>Village Data</title>
        <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container">
            <h1>Villages by Alliance</h1>
            <div class="accordion" id="accordionExample">
    """

    for i, (alliance, villages) in enumerate(villages_by_ally.items()):
        html_content += f"""
        <div class="card">
            <div class="card-header" id="heading{i}">
                <h2 class="mb-0">
                    <button class="btn btn-link" type="button" data-toggle="collapse" data-target="#collapse{i}" aria-expanded="true" aria-controls="collapse{i}">
                        {alliance}
                    </button>
                </h2>
            </div>
            <div id="collapse{i}" class="collapse" aria-labelledby="heading{i}" data-parent="#accordionExample">
                <div class="card-body">
                    <ul>
        """
        for village in villages:
            tribe = village_details.get((int(village['coordinates'][1:-1].split(',')[0]), int(village['coordinates'][1:-1].split(',')[1])), 'Unknown Tribe')
            html_content += f"<li>{village['coordinates']} - {village['player']} - {tribe} - <a href='{village['link']}' target='_blank'>Link</a></li>"

        html_content += """
                    </ul>
                </div>
            </div>
        </div>
        """

    html_content += """
            </div>
            <h1>Villages without Alliance</h1>
            <ul>
    """

    for village in no_ally_villages:
        tribe = village_details.get((int(village['coordinates'][1:-1].split(',')[0]), int(village['coordinates'][1:-1].split(',')[1])), 'Unknown Tribe')
        html_content += f"<li>{village['coordinates']} - {village['player']} - {tribe} - <a href='{village['link']}' target='_blank'>Link</a></li>"

    html_content += """
            </ul>
        </div>
        <script src="https://code.jquery.com/jquery-3.3.1.slim.min.js"></script>
        <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """

    file_path = filedialog.asksaveasfilename(defaultextension=".html", filetypes=[("HTML files", "*.html")])
    if file_path:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print("HTML report generated!")

def refresh_session(session, site_url):
    refresh_url = f"{site_url}/keep_alive.php" 
    try:
        session.get(refresh_url)
        print("Session refreshed.")
    except Exception as e:
        print(f"Failed to refresh session: {e}")

def keep_session_alive(session, site_url, interval=300):
    while True:
        refresh_session(session, site_url)
        time.sleep(interval)

def login_to_travian(username, password, site_url):
    login_url = f'{site_url}/login.php'
    session = requests.Session()

    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64)',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'en-GB,en;q=0.9',
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    login_payload = {
        'name': username,
        'password': password,
        's1': 'ورود',
    }

    login_response = session.post(login_url, headers=headers, data=login_payload)

    if 'SESS_ID' in session.cookies.get_dict():
        print("Logged in successfully")
        return session
    else:
        print("Login failed")
        return None

# اجرای GUI
def run_gui():
    def run_script():
        username = username_var.get()
        password = password_var.get()
        x_origin = int(x_origin_var.get())
        y_origin = int(y_origin_var.get())
        radius = int(radius_var.get())
        quadrant_choice = quadrant_var.get()
        quadrant_key = quadrant_choice.split()[0]
        quadrant_map = {'1': 'NE', '2': 'SE', '3': 'NW', '4': 'SW'}
        quadrant = quadrant_map[quadrant_key]
        site_url = site_url_var.get()
        session = login_to_travian(username, password, site_url)
        if session:
            refresh_thread = threading.Thread(target=keep_session_alive, args=(session, site_url))
            refresh_thread.daemon = True
            refresh_thread.start()

            unique_villages, villages_by_ally, no_ally_villages = fetch_map_data(session, site_url, x_origin, y_origin, radius, quadrant, progress_bar, terminal)
            
            village_details = fetch_village_tribes(session, site_url, unique_villages, terminal)
            
            generate_html_report(villages_by_ally, no_ally_villages, village_details)
            messagebox.showinfo("Success", "HTML report generated successfully!")

    def run_thread():
        thread = threading.Thread(target=run_script)
        thread.start()

    root = Tk()
    root.title("Travian Map Scanner")
    root.geometry("800x500")
    padding = {'padx': 20, 'pady': 10}

    Label(root, text="Username").grid(row=0, column=0, **padding)
    username_var = StringVar()
    Entry(root, textvariable=username_var).grid(row=0, column=1, **padding)

    Label(root, text="Password").grid(row=1, column=0, **padding)
    password_var = StringVar()
    Entry(root, textvariable=password_var, show="*").grid(row=1, column=1, **padding)

    Label(root, text="Travian Site URL").grid(row=2, column=0, **padding)
    site_url_var = StringVar()
    Entry(root, textvariable=site_url_var).grid(row=2, column=1, **padding)

    Label(root, text="Origin X").grid(row=3, column=0, **padding)
    x_origin_var = StringVar()
    Entry(root, textvariable=x_origin_var).grid(row=3, column=1, **padding)

    Label(root, text="Origin Y").grid(row=4, column=0, **padding)
    y_origin_var = StringVar()
    Entry(root, textvariable=y_origin_var).grid(row=4, column=1, **padding)

    Label(root, text="Radius").grid(row=5, column=0, **padding)
    radius_var = StringVar()
    Entry(root, textvariable=radius_var).grid(row=5, column=1, **padding)

    Label(root, text="Quadrant").grid(row=6, column=0, **padding)
    quadrant_var = StringVar()
    quadrant_dropdown = ttk.Combobox(root, textvariable=quadrant_var)
    quadrant_dropdown['values'] = ('1 (NE)', '2 (SE)', '3 (NW)', '4 (SW)')
    quadrant_dropdown.grid(row=6, column=1, **padding)
    quadrant_dropdown.current(0)

    Button(root, text="Run", command=run_thread).grid(row=7, column=0, columnspan=2, **padding)
    progress_bar = ttk.Progressbar(root, mode='indeterminate')
    progress_bar.grid(row=8, column=0, columnspan=2, **padding)

    terminal = Text(root, height=20, width=50, state="disabled")
    terminal.grid(row=0, column=2, rowspan=9, padx=20, pady=10)
    scrollbar = Scrollbar(root, command=terminal.yview)
    terminal.config(yscrollcommand=scrollbar.set)

    version_label = Label(root, text="Version 2.0 - © 2024 Afshin Mental", fg="gray", font=("Arial", 10))
    version_label.grid(row=9, column=0, columnspan=2, padx=20, pady=10)


    root.mainloop()

if __name__ == "__main__":
    run_gui()
