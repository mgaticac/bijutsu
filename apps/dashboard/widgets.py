from django.forms import ClearableFileInput

class ImagePreviewInput(ClearableFileInput):
    template_name = 'dashboard/widgets/image_input.html'
