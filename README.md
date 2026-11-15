# Browser Racing

A lightweight browser-based 3D driving game built with Three.js and cannon-es physics. It includes a 1,000 km by 1,000 km open world, a large highway network, unrestricted off-road driving, three camera views including first person, vehicle damage, changing weather, graphics presets, and responsive touch controls.

## Run locally

On Windows, double-click `run_game.bat`, or run:

```powershell
pip install -r requirements.txt
python server.py
```

Then open <http://localhost:5000>. To play on another phone, tablet, or computer on the same Wi-Fi network, open `http://YOUR-PC-IP:5000` on that device.

Browser Racing stays on the root route `/`.

Memory Ammunition is available at `/memory-ammunition`. Use memory rounds to record witnesses, replay the evidence, and reveal hidden threats.

Lanternbound is available at `/lanternbound`. Explore the Hushwood, then resolve a guardian encounter through listening, striking, or mercy.

Pulse Arena is available at `/pulse-arena`. This original 2D ball-parry game pits you against five bots. Move with WASD or arrow keys, aim with the mouse, and press Space, F, or click the arena to parry when the red ball enters your shield ring. You can only parry a ball targeting you. A late, close-range parry is perfect and recovers faster. Each deflection speeds up the ball; one hit eliminates a contender. After every elimination, the ball resets to its original base speed of 225 units per second; active ability effects still apply. Press Q or Shift to use your equipped ability and Esc to pause. Phones and tablets have movement, parry, and ability buttons.

Choose **Play with Bots** for a solo match, or **Play Online with Friends** to
create or join a private room. Share the invite link or six-character code;
the host starts the match and bots fill unused slots up to six contenders.
Online movement, ball targeting, abilities, eliminations, and coin awards are
controlled by the server. Eliminated players spectate until the round finishes.
If a player leaves, a bot takes over and the host role transfers if necessary.
Your online menu does not pause other players; shop changes are made between rounds.

For computers on the same network, use `http://YOUR-PC-IP:PORT/pulse-arena` with
the server's actual port (5000 by default). For different networks, deploy the
Python web service and share its public HTTPS game URL. See
[Render deployment and pulsearena.com setup](DEPLOYMENT.md). A localhost link
only works on the computer running the server; this project does not itself
register the domain or provision a hosting account.

Earn **20 coins for each elimination caused by your last return** and **60 coins per win**. Bots eliminating each other do not award you coins. The shop offers ten colors and five shaded, detailed cosmetic models (Pulse, Robot, Bear, Fox, and Dragon), with glowing cores, mechanical panels, fur, facial features, wings, and scales. The shop previews and in-arena avatars use the same artwork; colors and models can be mixed without changing hitboxes. Coins, wins, purchases, and equipped items save in the current browser. Opening the shop pauses the round; closing it leaves the round paused. Unavailable or damaged browser storage displays a warning; resetting saved progress requires confirmation.

Equip one ability at a time. **Dash** is owned for free from the start. Buy **Shield** (automatically return one incoming ball within 3 seconds), **Chain** (immediately make a ball targeting someone else target you), **Freeze** (stop the ball for 1.5 seconds), **Slow Motion** (45% ball speed for 3 seconds), **Blink** (teleport in your facing direction), or **Power Strike** (add 100 speed to your next manual return within 6 seconds). Each ability has a cooldown; swapping abilities does not bypass it. Shield only returns a ball when you are its target. No ability grants permanent invincibility.

The Three.js and cannon-es modules load from jsDelivr, so an internet connection is needed when the game starts.




## Controls

| Control | Action |
| --- | --- |
| `W` / Up arrow | Throttle |
| `S` / Down arrow | Brake and reverse |
| `A`, `D` / arrow keys | Steer |
| `Space` | Handbrake |
| `Shift` | Run while exploring on foot |
| `C` | Change camera |
| `R` | Recover to the road |
| `M` | Open or close the world map |
| `E` | Exit the stopped car or enter it again when nearby |
| `F` | Talk to or challenge a nearby person |
| `Esc` | Pause and open settings |

When outside the car, use **W/S** to walk forward or backward, **A/D** to turn, and hold **Shift** to run. Fifty named drivers live around the county's cities. Approach one and press **F** to talk, then press **F** again to challenge them. Return to your car and enter it to begin a one-on-one race. The garage includes saved driver customization for skin tone, shirt color, and trousers color.

Explore in any direction while the HUD tracks distance and world coordinates. Open the map and click or tap any city, landmark, or event marker to set a destination; the HUD arrow guides you there and clears when you arrive. Press `R` to recover to the nearest highway. Phones and tablets get on-screen controls for steering, throttle, brake, drifting, running, talking, entering or exiting the car, camera, recovery, the world map, and the garage.

Standard gamepads are supported: left stick or D-pad steers, triggers brake and accelerate, A/B drifts, X changes camera, Y recovers, and Menu pauses.

Handling becomes progressively less stable above 30% of each car's top speed: steering responds more slowly, available steering angle decreases sharply, and hard inputs create substantial lateral slip. Gentle steering remains normal cornering; a drift requires at least 55% steering input, with power drifts requiring 0.25 seconds of committed steering. During a drift, the front wheels countersteer and the rear tires leave paired skid marks on paved surfaces. Every vehicle has a shorter showroom-listed spinout time. Trucks and vans lose control sooner, while muscle and rally cars tolerate longer slides. Handling upgrades extend the time limit, and straightening early drains the buildup.

Open the pause menu to enter the full-screen garage. Switch between the dedicated **Car Showroom** and **Bike Showroom**, then use the arrow controls or filtered vehicle list to inspect each rotating model and its performance stats. The garage includes 100 cars and 50 rideable motorcycles: 20 Sport Bikes, 15 Drift Bikes, and 15 Adventure Bikes. Drift Bikes have stronger slides, lower drift-entry speeds, and longer spinout windows as their price increases. One bike from each class is free and permanently owned: **Apex 1** (Sport), **Slidefire** (Drift), and **Ember 1** (Adventure). Cars retain their distinct cockpit details, while bikes use an open first-person riding view.

Progress saves automatically in the browser every five seconds and when the page closes. Credits, purchased cars, difficulty, selected vehicle, world position, distance, damage, weather, and camera view return on the next visit. Use **Save Progress** in the garage to save immediately. Saves belong to the current browser and device.

Every **5 lifetime miles** driven awards one upgrade point. Spend points in the garage on Speed, Acceleration, Handling, or Off-road performance. Each category has five levels for every car, and upgrades remain attached to that car in the saved game. Restarting does not reset lifetime mileage or earned upgrades.

## Open-world events

Drive into a labeled event ring, then press its on-screen entry button to start with any car. Eight drift challenges score speed, angle, and sustained slides on their intended surface. **Canyon Drift Zone**, **Summit Switchbacks**, and **Crosscounty Drift** are off-road courses; the other five are paved road courses. Slides on the wrong surface earn no points. Each follows a 1,200-meter course with six ordered checkpoint gates. Every gate has a 10-second deadline that resets when the gate is reached; missing it ends the run as a DNF. Remaining gates appear in cyan, while the next gate is larger and bright green; reaching the final gate completes the run.

Seventeen checkpoint races run against three opponents. Six are dedicated straight-line drag races: **Redline Drag Strip**, **Runway Thunder Drag**, **Harbor Haul Drag**, **Northern Mile Drag**, **Eastline Launch Drag**, and **Southbound Street Drag**. The other eleven races use curved, multi-segment routes: **Ridge Rally Rush**, **Browser Racing Sprint**, **Metro Circuit**, **Dustline Dash**, **Coastal Velocity**, **County Endurance**, **Harborline Sprint**, **Ridgeway Run**, **Sunset Grand Tour**, **Pine Barrens Rally**, and **Meadowstorm Rally**. Grass events are rally races with rally opponents, while paved events use sport and hypercar opponents. The player's selected car is never restricted. Every remaining checkpoint is visible in cyan, while the next required checkpoint is larger and bright green. Each race starts with a **3-2-1-GO** countdown that holds every car on the grid before the timer begins. The HUD shows live position, checkpoints, and race time.

The county contains **30 labeled destinations** to discover, including lakes, wind farms, service stations, festival grounds, signal towers, ruins, observatories, lighthouses, airfields, and quarries. Each destination has detailed scenery and animated elements. **Ten cities** add dense urban blocks, skyscrapers, and paved street grids connected to the main highway, with intersections and asphalt handling. Buildings, trees, rocks, ruins, and solid landmark structures have physics hitboxes and cause impact damage. Reaching a landmark for the first time awards **CR 750**, and discoveries are saved.

Completing a race awards base payouts of **CR 5,000** for first, **CR 3,000** for second, **CR 2,000** for third, and **CR 1,000** for fourth. A timeout does not pay. Drift Zones award base payouts of **CR 1,500** for one star, **CR 2,750** for two stars, and **CR 4,000** for three stars.

## Difficulty

Choose a difficulty from the pause menu. **Easy** has fast rivals, tough drift targets, and standard rewards. **Normal** has elite rivals, high drift targets, and 1.25x rewards. **Hard** has extreme rivals, master-level drift targets, and 1.75x rewards. **Expert** raises the challenge further with 2.25x rewards. **Extreme** is the maximum challenge and pays 3x rewards. The selected difficulty is saved and takes effect when the next event starts.

## Performance

Open the pause menu and select **Low** graphics for integrated or older GPUs. This lowers pixel density and disables dynamic shadows while preserving the driving simulation.