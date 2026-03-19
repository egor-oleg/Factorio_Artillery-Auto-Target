Installation

   1. Install Python from python.org.
   2. run the Artillery-Auto-Target.py script using python

How to use

   1. Run the script: python Artillery-Auto-Target.py
   2. Open Factorio map and hold your Artillery Remote.
   3. Press F6 and drag a box over the area you want to hit.

Key		Context		Action

F6		   Always		Start Selection (Drag Box)
F5		   Always		Emergency Stop
TAB		Preview		Toggle Mode: Uniform (Area) / Center (Cluster)
SHFT+TAB	Preview		Lumberjack Mode: Target trees
S		   Preview		Pathing: Smart (Nearest) / Direct (Rows)
MWheel	Preview		Adjust Shot Density
ENTER		Preview		Confirm & Fire

L-Click		Preview		Cancel Selection

⚠️
If the script doesn't find nests, check Factorio color settings or enter your own values in the line:
ENEMY_COLORS = [(158, 20, 20), (250, 28, 29),]
