def pyside_word_wrap(text, font_family, width, height,
                     line_spacing_ratio, outline_width, bold, italic, underline,
                     alignment, direction,
                     max_font_size=40, min_font_size=9, margin=10):
     """
     Ajuste la taille de la police pour que le texte rentre dans un rectangle donné.
     Prend en compte le retour à la ligne automatique.
     """
     # Appliquer une marge de sécurité
     width -= 2 * margin
     height -= 2 * margin
 
     # Initialisation de QFont
     font = QFont(font_family)