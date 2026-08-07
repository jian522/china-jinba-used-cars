import urllib.request, re
print("=== Checking deployed cars.html ===")
html = urllib.request.urlopen("https://jinbacars.com/cars.html").read().decode("utf-8")
m = re.search(r'function renderCars.*?(?=function filterCars)', html, re.DOTALL)
if m:
    func = m.group()
    print(f"renderCars found: {len(func)} chars")
    print("c.image:", "OK" if "c.image" in func else "MISSING!")
    print("img tag:", "OK" if "<img" in func else "MISSING!")
    print("c.badge:", "BUG!" if "c.badge" in func else "OK")
    print("c.brandEn:", "BUG!" if "c.brandEn" in func else "OK")
    print("c.fuel (no _type):", "BUG!" if "c.fuel" in func and "c.fuel_type" not in func else "OK")
else:
    print("renderCars NOT FOUND!")
    all_scripts = re.findall(r'<script>(.*?)</script>', html, re.DOTALL)
    print(f"Script blocks: {len(all_scripts)}")

print("\n=== Checking deployed cars-detail.html ===")
html2 = urllib.request.urlopen("https://jinbacars.com/cars-detail.html").read().decode("utf-8")
scripts2 = re.findall(r'<script>(.*?)</script>', html2, re.DOTALL)
for s in scripts2:
    if "car." in s or "CARS_DATA" in s:
        print(f"Detail script: {len(s)} chars")
        print("car.image:", "OK" if "car.image" in s else "MISSING!")
        print("img tag:", "OK" if "<img" in s else "MISSING!")
        print("badge (no is_):", "BUG!" if "badge" in s and "is_" not in s else "OK")
        break

print("\n=== Checking images online ===")
for img in ["car_1_1.jpg", "car_2_2.jpg", "car_100_100.jpg", "slide_1.jpg"]:
    try:
        data = urllib.request.urlopen(f"https://jinbacars.com/uploads/cars/{img}").read()
        print(f"  cars/{img}: OK ({len(data)} bytes)")
    except:
        try:
            data = urllib.request.urlopen(f"https://jinbacars.com/uploads/carousel/{img}").read()
            print(f"  carousel/{img}: OK ({len(data)} bytes)")
        except:
            print(f"  {img}: NOT FOUND!")
