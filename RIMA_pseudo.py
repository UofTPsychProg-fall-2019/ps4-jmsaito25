#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov  5 17:08:01 2019

@author: jmsaito
"""

#In the following experiment, participants are tested on their ability to remember 
#colored circles over a brief interval. Specifically, each trial 
#begins with presenting a colored circle that the participants are asked to 
#remember the color of. There is a brief delay, and then participants report 
#their memory of the color by selecting a color from a color wheel and submitting 
#a confidence rating in this memory report. In the critical trials, participants 
#are presented with a novel-colored probe circle during the delay and asked to 
#subjectively indicate if the probe’s color is similar or dissimilar to the one they 
#are trying to remember. The goal is to determine if directly accessing the 
#memory during the similarity judgment influences participants’ memory of the 
#target color.

import numpy as np
import random
import psychopy.visual
import psychopy.event
import pandas as pd
import math
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import cm
import win32api

##############################################################################
# Set up subject data arrays
##############################################################################

sub = 1 # Need to change manually or use a prompt
trial = [] #Trial number
target_color = [] #Color of the target in degrees
probe_type = [] #0 control, 1 (16-45 degrees), 2 (46-75 degrees), 3 (76-105 degrees)
probe_direction = [] # 0 control, 1 clockwise, 2 counterclockwise
probe_offset = [] # Offset in degrees of probe relative to target, control = 0
probe_degrees = [] # Color of the probe in degrees, control = 0
probe_response = [] # 0 = control/no response, 1 similar, 2 dissimilar
recall_response = [] #Color of final recall response in degrees
recall_confidence = [] #Confidence rating of final resp 1 high, 2 somewhat, 3 guess

# Create dictionary that contains degree:rgb values
degrees = list(range(1,360))

# The following contains a for loop that iterates through each degree from 1-360
# and calculates the RGB color valuea for that degree in circular color space
# Degree is converted to HSV color space which is converted to RGB color space
# Degree = Hue in HSV (Hue, Saturation, Value)
# For details on this conversion, see 
# https://en.wikipedia.org/wiki/HSL_and_HSV#HSV_to_RGB
# The particular algorithm employ belowed is adapted from 
# https://python-forum.io/Thread-Python-function-to-get-colorwheel-RGB-values-from-compass-degree

degree_rgb = pd.DataFrame(columns =('r','g','b')) #Initialize a dataframe to store degree:RGB
for x in degrees: #For 1-360, convert each degree to its respective RGB value
    hue_int = float(x) 
    saturation = float(1) #Saturation & Value are consistently maximized at '1'
    value = float(1)
    hue_conv = hue_int/60.0
    hue_conv_min = math.floor(hue_conv)
    hue_min_mod = int(hue_conv_min) % 6
    f = hue_conv - hue_min_mod
    p = value * (1 - saturation)
    q = value * (1 - f * saturation)
    t = value * (1 - (1 - f) * saturation)
    r = 0
    g = 0
    b = 0
    if hue_min_mod == 0:
        r = value
        g = t 
        b = p
    elif hue_min_mod == 1:
        r = q
        g = value
        b = p
    elif hue_min_mod == 2:
        r = p
        g = value
        b = t
    elif hue_min_mod == 3:
        r = p
        g = q
        b = value
    elif hue_min_mod == 4:
        r = t
        g = p
        b = value
    elif hue_min_mod == 5:
        r = value
        g = p
        b = q
        
    r, g, b = int(r * 255), int(g * 255), int(b * 255)
    degree_rgb.set_value(x, 'r', r)
    degree_rgb.set_value(x, 'g', g)
    degree_rgb.set_value(x, 'b', b)

numtrials = 200 #50 control, 150 experimental (50 high sim, 50 med sim, 50 low sim)
seed = sub # Seed the random number generator using subject number
random.seed(sub)

# Generate all the target stimuli colors (in degrees)
for x in range(1, numtrials+1): #Use +1 to make sure it creates a 200 item list
    current_degree = random.randint(1,360)
    target_color.append(current_degree)

# Create array that determines if trial will be control or experimental
probe_type = np.zeros(200) #
probe_type[:50] = 1 # High Similar Probe (15-45 degrees offset)
probe_type[50:100] = 2 # Medium Similar Probe (46 - 75 degrees offset)
probe_type[100:150] = 3 # Low Similar Probe (76 - 105 degrees offset)
np.random.shuffle(probe_type)

#Initiate probe offset array
probe_offset = np.zeros(200)

# Loop through probe_degree and replace the condition with a random degree value
for x in range(1, len(probe_type)):
    if probe_type[x] == 0:
        continue
    if probe_type[x] == 1:
        probe_offset[x] = random.randint(15,45)
    elif probe_type[x] == 2:
        probe_offset[x] = random.randint(46,75)
    elif probe_type[x] == 3:
        probe_offset[x] = random.randint(76,105)
        
###########################################################################
# Set up trials
############################################################################
#Trial consists of:
#1. ITI (blank screen time between starting trial w spacebar & target onset)
#2. Target presentation (target on screen for 1.6 seconds)
#3. ISI 1 (blank screen time between target offset and probe onset)
#4. Probe presentation (probe on screen for 1.6 seconds)
#5. ISI 2 (blank screen time between probe offset and color wheel onset)
#6. Color Wheel presentation (offset by mouse click on wheel, time unlimited)
#7. Adjust Period (present color of click, allow for adjusting, time unlimited)
#    - Includes looking for confidence rating (indicated w/ button press)
#8. End of Trial (blank screen time between answer offset and begin next trial w/ spacebar)
       
# Set up Durations
iti_dur = 0.4 #Intertrial interval duration
target_dur = 1.6 #Target stimulus presentation duration
isi = 0.8 #Pre-/post-probe ISI
probe_dur = 1.6 #Probe stimulus presentation duration

#Colors in [R G B]
BackgroundColor = [255, 255, 255] #white
FixationColor = [0, 0, 0] #black

###########################################################################
# Loop trials and present stimuli 
###########################################################################
for x in range (1, numtrials):
    # Wait for subject to begin trial
    keys = psychopy.event.getKeys(keys =["space"])
    if keys == "space":
        continue
    else:
        keys = psychopy.event.getKeys(keys =["space"])

#####
# ITI
#####
    
    #Draw blank screen
    win = psychopy.visual.Window(
        size=[1440, 900], #Change this to screen size 
        units="pix", #Set units as pixels
        fullscr=True, #Fill screen with window
        color=BackgroundColor #Set background color as white
        )
    
    #Draw Fixation Cross
    fixation = psychopy.visual.GratingStim(win=win, 
            size=0.5, 
            pos=[0,0], 
            sf=0, 
            rgb=FixationColor)
    
    fixation.draw()
    
    #Set the clock
    clock = psychopy.core.Clock()
    clock.reset()
    
    #Present ITI blank screen
    while clock.getTime() < iti_dur:
        win.flip()

    #After ITI ends, close window & reset clock
    win.close()
    clock.reset()
    
#####
# Present Target
#####

   #Draw blank screen
    win = psychopy.visual.Window(
        size=[1440, 900], 
        units="pix", 
        fullscr=True, 
        color=BackgroundColor 
        )
    
    #Draw Target Circle on screen
    
    #   Grab circle color
    current_targ_degree = target_color[x-1]
    current_targ_color = [(degree_rgb['r'][current_targ_degree]),
                          (degree_rgb['g'][current_targ_degree]),
                          (degree_rgb['b'][current_targ_degree])
                         ]
    
    #   Draw circle in designated color
    circle = psychopy.visual.Circle(
        win=win,
        units="pix",
        radius=150, #Adjust circle radius to fit suitable size
        fillColor=[current_targ_color],
        edges=128
        )
    
    circle.draw()
    
    #Reset the clock
    clock = psychopy.core.Clock()
    clock.reset()

    #Present the target circle for the intended duration
    while clock.getTime() < target_dur:
        win.flip()

    #Close the window once presentation of the target ends
    win.close()

#####
# ISI 1
#####
    #Draw blank screen
    win = psychopy.visual.Window(
        size=[1440, 900], #Change this to screen size 
        units="pix", #Set units as pixels
        fullscr=True, #Fill screen with window
        color=BackgroundColor #Set background color as white
        )
    #Create and Draw Fixation Cross
    fixation = psychopy.visual.GratingStim(win=win, 
            size=0.5, 
            pos=[0,0], 
            sf=0, 
            rgb=FixationColor)
    
    fixation.draw()
    
    #Reset the clock
    clock = psychopy.core.Clock()
    clock.reset()
    
    #Present fixation cross on white screen for intended ISI
    while clock.getTime() < isi:
        win.flip()
      
    #Close window once ISI ends
    win.close()
  
#####
# Recognition Probe
#####

    #Check if probe is present (experimental trial) or not (control)
    #If control, set response/probe degrees to zero and extend delay interval
    if probe_type[x-1] == 0.0:
        probe_direction.append('0')
        probe_degrees.append('0')
        probe_response.append('0')
        
        win = psychopy.visual.Window(
            size=[1440, 900],
            units="pix",
            fullscr=True, 
            color=BackgroundColor 
            )
   
        #Reset the clock
        clock = psychopy.core.Clock()
        clock.reset()

        while clock.getTime() < probe_dur:
            win.flip()
            
        win.close()
    elif probe_type[x-1] == 1 or probe_type[x-1] == 2 or probe_type[x-1] == 3 :
        #Determine if the offset of probe will be CW or CCW
        direction = ("CW","CCW")
        decide = random.choice(direction)
        
        #Depending on CW/CCW, determine probe color in degrees
        if decide == "CW":
            current_probe_degree = (target_color[x-1]) + (probe_offset[x-1])
            probe_direction.append('1')
            probe_degrees.append(current_probe_degree)
        elif decide == "CCW":
            current_probe_degree = (target_color[x-1]) - (probe_offset[x-1])
            probe_direction.append('2')
            probe_degrees.append(current_probe_degree)
            
        #Set up probe screen
        win = psychopy.visual.Window(
            size=[1440, 900], #Change this to screen size 
            units="pix", #Set units as pixels
            fullscr=True, #Fill screen with window
            color=BackgroundColor #Set background color as white
            )

        #Grab the color information for the current probe
        current_targ_color = [(degree_rgb['r'][current_probe_degree]),
                          (degree_rgb['g'][current_probe_degree]),
                          (degree_rgb['b'][current_probe_degree])
                          ]
    
        #Set up the target circle with the probe color
        circle = psychopy.visual.Circle(
            win=win,
            units="pix",
            radius=150, #Adjust circle radius to fit suitable size
            fillColor=[current_targ_color],
            edges=128
            )
        
        circle.draw()   
        
        #Reset the clock
        clock = psychopy.core.Clock()
        clock.reset()

        #Present the probe circle for the intended duration
        while clock.getTime() < target_dur:
            win.flip()
            keys = psychopy.event.getKeys(keyList = ["1","0"])
        
        #Add recognition response to list
        if keys == '1' or keys == '0':
            probe_response.append(keys)
        elif keys == []:
            probe_response.append('none')
            
        keys = [] #reset keys
        
        #Close the window once presentation of the probe ends
        win.close()

#####
# ISI 2
#####
    #Draw blank screen
    win = psychopy.visual.Window(
        size=[1440, 900], #Change this to screen size 
        units="pix", #Set units as pixels
        fullscr=True, #Fill screen with window
        color=BackgroundColor #Set background color as white
        )
    #Create and Draw Fixation Cross
    fixation = psychopy.visual.GratingStim(win=win, 
            size=0.5, 
            pos=[0,0], 
            sf=0, 
            rgb=FixationColor)
    
    fixation.draw()
    
    #Reset the clock
    clock = psychopy.core.Clock()
    clock.reset()
    
    #Present fixation cross on white screen for intended ISI
    while clock.getTime() < isi:
        win.flip()
      
    #Close window once ISI ends
    win.close()

#####
# Draw color wheel
#####
    
    #MATLAB version; need to figure out if this is similar format   
    #Screen('FrameArc',wPtr,[ZL_colors.R(i) ZL_colors.G(i) ZL_colors.B(i)], 
    #[screencenter(1)-probe_dist screencenter(2)-probe_dist  screencenter(1)+probe_dist 
    #screencenter(2)+probe_dist], [90+i], [1], [probe_size/2]);

    #To draw circle, begin at center of the screen and move out at a 0 degree angle
    #(i.e., right) the length of the inner radius and begin drawing a 1 degree 
    #arc that contains the color for each respective degree 

    #Sample code for drawing color wheel below from: 
    #https://stackoverflow.com/questions/31940285/plot-a-polar-color-wheel-based-
    #on-a-colormap-using-python-matplotlib

    win = psychopy.visual.Window(
        size=[1440, 900], #Change this to screen size 
        units="pix", #Set units as pixels
        fullscr=True, #Fill screen with window
        color=BackgroundColor #Set background color as white
        )
    
    display_axes = plt.figure.add_axes([0.1,0.1,0.8,0.8], projection='polar')
    display_axes._direction = 2*np.pi 
    norm = mpl.colors.Normalize(0.0, 2*np.pi)
    quant_steps = 2056
    cb = mpl.colorbar.ColorbarBase(display_axes, cmap=cm.get_cmap('hsv',quant_steps),
                                   norm=norm,
                                   orientation='horizontal')                                  
    cb.outline.set_visible(False)                                 
    display_axes.set_rlim([-1,1])
    plt.show()
    
    win.flip()
    
    #Show Mouse cursor
    psychopy.event.Mouse(visible=True)
    
    #Check if mouse is clicked inside wheel and grab the coordinate of the click
    if psychopy.mouse.isPressedIn(plt, buttons=[0]):
        x,y = win32api.GetCursorPos()
        
    #Convert x,y to angle, convert angle to RGB
    click_radian = math.atan2(y,x) #Use arctan function to determine radian
    click_degrees = math.degrees(click_radian) #Convert this radian to degrees
    current_degrees = click_degrees #Set current degrees
    click_color = [(degree_rgb['r'][current_degrees]),
                   (degree_rgb['g'][current_degrees]),
                   (degree_rgb['b'][current_degrees])
                  ]
    
    #Clean up (hide cursor, close color wheel)
    psychopy.event.Mouse(visible=False)
    plt.close()
    
    #Draw tentative answer circle in color selected
    circle = psychopy.visual.Circle(
            win=win,
            units="pix",
            radius=150, #Adjust circle radius to fit suitable size
            fillColor=[click_color],
            edges=128
            )
    
    circle.draw()
    win.flip()
    
    #Allow for hue adjusting with arrow keys OR final answer w/ confidence rating
    keys = psychopy.event.getKeys(keys =["left","right", "1","2","3"])
    while not keys == '1' or keys == '2' or keys == '3':
        keys = psychopy.event.getKeys(keys =["left","right", "1","2","3"])
        if keys == "left": #Adjust the color one degree to CCW
            current_degrees = current_degrees - 1
            current_color = [(degree_rgb['r'][current_degrees]),
                   (degree_rgb['g'][current_degrees]),
                   (degree_rgb['b'][current_degrees])
                   ]
            circle = psychopy.visual.Circle(
                    win=win,
                    units="pix",
                    radius=150, #Adjust circle radius to fit suitable size
                    fillColor=[current_color],
                    edges=128
                    )
            circle.draw()
            win.flip()
            
        elif keys == "right":
            current_degrees = current_degrees + 1 #Adjust color one degree CW
            current_color = [(degree_rgb['r'][current_degrees]),
                   (degree_rgb['g'][current_degrees]),
                   (degree_rgb['b'][current_degrees])
                   ]
            circle = psychopy.visual.Circle(
                    win=win,
                    units="pix",
                    radius=150, #Adjust circle radius to fit suitable size
                    fillColor=[current_color],
                    edges=128
                    )
            circle.draw()
            win.flip()
            
    #If they indicate confidence, end trial and collect response/confidence
    if keys == '1' or keys == '2' or keys == '3':
        recall_confidence.append(keys)
        recall_response.append(current_degrees)
        win.close()

##############################################################################
# End Experiment & Save out Data File
##############################################################################
indiv_rima = pd.Dataframe(columns = ['trial','target_color','probe_type','probe_direction',
                           'probe_offset','probe_degrees', 'probe_response',
                           'recall_response', 'recall_confidence'])
for x in range(1,200):
    indiv_rima.trial[x] = x
    indiv_rima.target_color[x] = target_color[x]
    indiv_rima.probe_type[x]= probe_type[x]
    indiv_rima.probe_direction[x]= probe_direction[x]
    indiv_rima.probe_offset[x]= probe_offset[x]
    indiv_rima.probe_degrees[x]= probe_degrees[x]
    indiv_rima.probe_response[x]= probe_response[x]
    indiv_rima.recall_response[x]= recall_response[x]
    indiv_rima.recall_confidence[x]= recall_confidence[x]
    
indiv_rima.to_csv('\Users\jmsaito\Documents\GitHub\ps4-jmsaito25\indiv_rima.csv')


