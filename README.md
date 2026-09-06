# Browser Racing

A lightweight browser-based 3D driving game built with Three.js and cannon-es physics. It includes a 1,000 km by 1,000 km open world, a large highway network, unrestricted off-road driving, three camera views including first person, vehicle damage, changing weather, graphics presets, and responsive touch controls.

## Run locally

On Windows, double-click `run_game.bat`, or run:

```powershell
pip install -r requirements.txt
python server.py
```

Then open <http://localhost:5000>. To play on another phone, tablet, or computer on the same Wi-Fi network, open `http://YOUR-PC-IP:5000` on that device.

The Three.js and cannon-es modules load from jsDelivr, so an internet connection is needed when the game starts.

## Controls

| Control | Action |
| --- | --- |
| `W` / Up arrow | Throttle |
| `S` / Down arrow | Brake and reverse |
| `A`, `D` / arrow keys | Steer |
| `Space` | Handbrake |
| `C` | Change camera |
| `R` | Recover to the road |
| `M` | Open or close the world map |
| `Esc` | Pause and open settings |

Explore in any direction while the HUD tracks distance and world coordinates. Open the map and click or tap any city, landmark, or event marker to set a destination; the HUD arrow guides you there and clears when you arrive. Press `R` to recover to the nearest highway. Phones and tablets get on-screen controls for steering, throttle, brake, drifting, camera, recovery, the world map, and the garage.

Standard gamepads are supported: left stick or D-pad steers, triggers brake and accelerate, A/B drifts, X changes camera, Y recovers, and Menu pauses.

Handling becomes progressively less stable above 30% of each car's top speed: steering responds more slowly, available steering angle decreases sharply, and hard inputs create substantial lateral slip. Gentle steering remains normal cornering; a drift requires at least 55% steering input, with power drifts requiring 0.25 seconds of committed steering. During a drift, the front wheels countersteer and the rear tires leave paired skid marks on paved surfaces. Every vehicle has a showroom-listed spinout time. Trucks and vans lose control sooner, while muscle and rally cars tolerate longer slides. Handling upgrades extend the time limit, and straightening early drains the buildup.

Open the pause menu to enter the full-screen garage showroom. Browse all 100 vehicles with the arrow controls or vehicle list, inspect each rotating 3D model and its performance stats, then buy or drive it. **Veloce**, **Mammoth**, and **Summit** are included as starter cars; the remaining garage spans rally GTs, muscle GTs, performance trucks, street vans, track supercars, and hypercars with progressively higher prices and performance.

Progress saves automatically in the browser every five seconds and when the page closes. Credits, purchased cars, difficulty, selected vehicle, world position, distance, damage, weather, and camera view return on the next visit. Use **Save Progress** in the garage to save immediately. Saves belong to the current browser and device.

Every **5 lifetime miles** driven awards one upgrade point. Spend points in the garage on Speed, Acceleration, Handling, or Off-road performance. Each category has five levels for every car, and upgrades remain attached to that car in the saved game. Restarting does not reset lifetime mileage or earned upgrades.

## Open-world events

Drive into a labeled event ring, then press its on-screen entry button to start with any car. Eight drift challenges score speed, angle, and sustained slides: **Canyon Drift Zone**, **Dockyard Slide**, **Summit Switchbacks**, **Midnight Burnout**, **Westgate Drift Yard**, **North Loop Slide**, **Crosscounty Drift**, and **Eastline Smoke Run**. Each has its own time limit and three-star targets.

Eleven checkpoint races run against three opponents: **Ridge Rally Rush**, **Browser Racing Sprint**, **Metro Circuit**, **Dustline Dash**, **Coastal Velocity**, **County Endurance**, **Harborline Sprint**, **Ridgeway Run**, **Sunset Grand Tour**, **Pine Barrens Rally**, and **Meadowstorm Rally**. Grass events are rally races with rally opponents, while paved events use sport and hypercar opponents. The player's selected car is never restricted. Every remaining checkpoint is visible in cyan, while the next required checkpoint is larger and bright green. Each race starts with a **3-2-1-GO** countdown that holds every car on the grid before the timer begins. The HUD shows live position, checkpoints, and race time.

The county contains **30 labeled destinations** to discover, including lakes, wind farms, service stations, festival grounds, signal towers, ruins, observatories, lighthouses, airfields, and quarries. Each destination has detailed scenery and animated elements. **Ten cities** add dense urban blocks, skyscrapers, and paved street grids connected to the main highway, with intersections and asphalt handling. Buildings, trees, rocks, ruins, and solid landmark structures have physics hitboxes and cause impact damage. Reaching a landmark for the first time awards **CR 750**, and discoveries are saved.

Completing a race awards base payouts of **CR 5,000** for first, **CR 3,000** for second, **CR 2,000** for third, and **CR 1,000** for fourth. A timeout does not pay. A three-star Drift Zone result awards a base **CR 4,000**.

## Difficulty

Choose a difficulty from the pause menu. **Easy** has fast rivals, tough drift targets, and standard rewards. **Normal** has elite rivals, high drift targets, and 1.25x rewards. **Hard** has extreme rivals, master-level drift targets, and 1.75x rewards. **Expert** raises the challenge further with 2.25x rewards. **Extreme** is the maximum challenge and pays 3x rewards. The selected difficulty is saved and takes effect when the next event starts.

## Performance

Open the pause menu and select **Low** graphics for integrated or older GPUs. This lowers pixel density and disables dynamic shadows while preserving the driving simulation.