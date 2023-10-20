from gradio.themes.utils.colors import Color
from gradio.themes import GoogleFont
from gradio.themes.base import Base

import matplotlib.colors as mcolors

# Define key parameters

brand_color = "#46A5FF"
font1 = GoogleFont('Inter')
font2 = GoogleFont('Besley')

# Construct brand color gradient

original_rgb = mcolors.to_rgb(brand_color)

fraction = 0.5
darker_list = []
lighter_list = []
while fraction < 1.6:
    if (fraction < 1):
        darker_rgb = tuple([x * fraction for x in original_rgb])
        darker_list.append(darker_rgb)
    if (fraction >= 1):
        lighter_rgb = tuple([x+(1-x)*(fraction-1) for x in original_rgb])
        lighter_list.append(lighter_rgb)
    
    fraction += 0.1

darker_list.reverse()
lighter_list.reverse()
rgb_list = lighter_list+darker_list

hex_list = [mcolors.to_hex(x) for x in rgb_list]
#print(hex_list)

custom_color = Color(
    name="custom_color",
    *hex_list
    )

class Seafoam(Base):
    pass

customtheme = Seafoam(primary_hue="custom_color",secondary_hue="custom_color",
    font=[font1, font2],
)