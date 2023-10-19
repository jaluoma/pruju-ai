from gradio.themes.utils.colors import Color
from gradio.themes import GoogleFont
from gradio.themes import Soft

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

aaltobluetheme = Soft(
    primary_hue="aaltoblue",#secondary_hue="aaltoblue",
    font=[GoogleFont('Inter'), GoogleFont('Besley')],
    text_size="sm",
)