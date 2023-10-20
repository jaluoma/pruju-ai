from gradio.themes.utils.colors import Color
from gradio.themes import GoogleFont
from gradio.themes import Soft
from gradio.themes.base import Base

brand_color = "#46A5FF"

aaltoblue = Color(
    name="aaltoblue",
    c50= "#ECF6FF",
    c100= "#D4E9FF",
    c200= "#A9D0FF",
    c300= "#7EB7FF",
    c400= "#539EFF",
    c500= "#46A5FF", # Aalto Blue
    c600= "#3A8FE6",
    c700= "#2F79CD",
    c800= "#2653B4",
    c900= "#1D2D9B",
    c950= "#141784",
    )



#aaltobluetheme = Soft(primary_hue="aaltoblue",secondary_hue="aaltoblue",
#    #primary_hue="aaltoblue",#secondary_hue="aaltoblue",
#    font=[GoogleFont('Inter'), GoogleFont('Besley')]
#    ,
#)

class Seafoam(Base):
    pass

aaltobluetheme = Seafoam(primary_hue="aaltoblue",secondary_hue="aaltoblue",
    font=[GoogleFont('Inter'), GoogleFont('Besley')],
)

#aaltobluetheme.background_fill_primary="white"
#aaltobluetheme.background_fill_primary_dark="black"

#aaltobluetheme.input_background_fill="white"
#aaltobluetheme.block_background_fill="blue"