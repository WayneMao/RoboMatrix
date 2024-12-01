SKILLS = ['<VLA>: move to <object1>',
          '<VLA>: grasp <object1>',
          '<VLA>: position <object1> Over the <object2>'
          '<VLA>: release the <object1>',
          '<VLA>: Open the drawer',
          '<VLA>: Close the drawer',
          '<shooting>: shooting <object1>',
          ]
# SKILLS = ['move to <object1>',
#           'grasp <object1>',
#           'position <object1> Over the <object2>'
#           'release the <object1>',
#           'shooting <object1>',
#           ]

# 'pick and place',
# 'lift the <object1>',
TASK = {
    '<VLA>': 1,
    '<shooting>': 2
}
META_SKILLS = ['turn left',
               'turn right',
               'go ahead',
               'go back',]

'''
1.Identify the Objects
2.Approach the Coca Can
3.Grab the Cola Can
4. Lift the Cola Can
5.Navigate to the White Box
6.Position the Can Over the Box
7.Release the Can
8.Ensure the Can is Inside
9.Finish Task
'''

'''
Move to the Red Cola Can.
Grasp the Red Cola Can.
Move to the White Box.
Position the Can Over the Box.
'''

'''
不分stage prompt:
Place the red cola can in front into the white box.
分stage：
Move to the red cola can, Grasp the red cola can, move to the white box, and place the red cola can into the white box.
'''