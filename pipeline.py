# Text Rendering
render_settings = self.main_page.render_settings()
upper_case = render_settings.upper_case
format_translations(blk_list, trg_lng_cd, upper_case=upper_case)
get_best_render_area(blk_list, image, inpaint_input_img)

font = render_settings.font_family
font_color = QColor(render_settings.color)

max_font_size = render_settings.max_font_size
min_font_size = render_settings.min_font_size
line_spacing = float(render_settings.line_spacing) 
outline_width = float(render_settings.outline_width)
outline_color = QColor(render_settings.outline_color) 
bold = render_settings.bold
italic = render_settings.italic
underline = render_settings.underline
alignment_id = render_settings.alignment_id
alignment = self.main_page.button_to_alignment[alignment_id]
direction = render_settings.direction
margin = render_settings.margin # Nouvelle variable
    
text_items_state = []
for blk in blk_list:
    x1, y1, width, height = blk.xywh

    translation = blk.translation
    if not translation or len(translation) == 1:
        continue

    translation, font_size = pyside_word_wrap(translation, font, width, height,
                                            line_spacing, outline_width, bold, italic, underline,
                                            alignment, direction, max_font_size, min_font_size,
                                            margin) # Passer la marge
    
    # Display text if on current page  
    if current_batch_file == file_on_display:
        self.main_page.blk_rendered.emit(translation, font_size, blk) 