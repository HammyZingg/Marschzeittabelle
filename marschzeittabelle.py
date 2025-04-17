import xml.etree.ElementTree as ET
from geopy.distance import geodesic
import csv

# --- EINSTELLUNGEN ---
GPX_FILE = "path/to/your/outdooractive_GPX_file"  # Ersetze durch den Pfad zu deiner GPX-Datei


# --- GPX LADEN ---
def load_gpx(file_path):
    ns = {'default': 'http://www.topografix.com/GPX/1/1'}
    tree = ET.parse(file_path)
    root = tree.getroot()
    trkpts = []

    for trk in root.findall('default:trk', ns):
        for seg in trk.findall('default:trkseg', ns):
            for idx, pt in enumerate(seg.findall('default:trkpt', ns)):
                lat = float(pt.attrib['lat'])
                lon = float(pt.attrib['lon'])
                ele = pt.find('default:ele', ns)
                name = pt.find('default:name', ns)
                trkpts.append({
                    'index': idx,
                    'lat': lat,
                    'lon': lon,
                    'ele': float(ele.text) if ele is not None else None,
                    'name': name.text if name is not None else None
                })
    return trkpts


# --- FIXPUNKTE FINDEN ---
def extract_fixed_points(trkpts):
    fixed = []
    for i, pt in enumerate(trkpts):
        if pt['name']:
            fixed.append({'name': pt['name'], 'index': i})
    return fixed


# --- DISTANZ & HÖHENUNTERSCHIED ---
def segment_stats(points):
    total_dist = 0.0
    gain = 0.0
    loss = 0.0

    for i in range(1, len(points)):
        a, b = points[i-1], points[i]
        dist = geodesic((a['lat'], a['lon']), (b['lat'], b['lon'])).km
        total_dist += dist
        ele_diff = b['ele'] - a['ele']
        if ele_diff > 0:
            gain += ele_diff
        else:
            loss += abs(ele_diff)

    return total_dist, gain, loss


# --- LEISTUNGSKILOMETER ---
def performance_km(dist_km, gain_m,loss_m):
    lkm =round(dist_km + (gain_m / 100.0) + (loss_m/1000.0), 2)
    return lkm


# --- ZEIT (NAISMITH) ---
def naismith_time(lkm):
    kmh = 4.0   # geschwindigkeit kann man hier ändern
    return lkm/kmh


# --- AUSGABE ---
def print_timetable(trkpts, fixed_points):
    print("\n=== Wander-Zeitplan ===\n")
    for i in range(len(fixed_points) - 1):
        start = fixed_points[i]
        end = fixed_points[i + 1]

        seg = trkpts[start['index']:end['index']+1]
        dist, gain, loss = segment_stats(seg)
        perf_km = performance_km(dist, gain, loss)
        time = naismith_time(perf_km)

        print(f"{start['name']} → {end['name']}")
        print(f"  Entfernung         : {dist:.2f} km")
        print(f"  Aufstieg           : {gain:.0f} m")
        print(f"  Abstieg            : {loss:.0f} m")
        print(f"  Leistungskilometer : {perf_km:.2f} km")
        print(f"  Zeitabschätzung    : {time:.2f} Stunden")
        print("-" * 40)


# --- AUSGABE ALS CSV ---
def save_timetable_to_csv(trkpts, fixed_points, output_file):
    with open(output_file, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Startpunkt", "Endpunkt", "Entfernung (km)", "Aufstieg (m)", "Abstieg (m)", "Leistungskilometer (km)", "Zeitabschätzung (Stunden)"])

        for i in range(len(fixed_points) - 1):
            start = fixed_points[i]
            end = fixed_points[i + 1]

            seg = trkpts[start['index']:end['index']+1]
            dist, gain, loss = segment_stats(seg)
            perf_km = performance_km(dist, gain, loss)
            time = naismith_time(perf_km)

            writer.writerow([start['name'], end['name'], f"{dist:.2f}", f"{gain:.0f}", f"{loss:.0f}", f"{perf_km:.2f}", f"{time:.2f}"])


# --- MAIN ---
if __name__ == "__main__":
    trkpts = load_gpx(GPX_FILE)
    fixed = extract_fixed_points(trkpts)

    if len(fixed) < 2:
        print("Nicht genug Fixpunkte gefunden (mindestens 2 erforderlich).")
    else:
        print_timetable(trkpts, fixed)
        output_file = "Path/to/your/folder"  # Specify the output CSV file path
        save_timetable_to_csv(trkpts, fixed, output_file)
        print(f"Zeitplan wurde in die Datei '{output_file}' gespeichert.")