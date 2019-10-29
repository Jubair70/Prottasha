from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout, Field
from onadata.apps.planmodule.helpers import DOCUMENT_TYPE

class MyColFormHelper(FormHelper):
    form_tag = False
    disable_csrf = True

class FileShareForm(forms.Form):
    title = forms.CharField(max_length=50)
    document_type = forms.ChoiceField(choices=DOCUMENT_TYPE, required=False)
    rpt_img_file = forms.FileField(required=False)
    shared_file = forms.FileField()

    def __init__(self, *args, **kwargs):
        super(FileShareForm, self).__init__(*args, **kwargs)
        self.fields['rpt_img_file'].label = "Latest Reports Image"
        self.helper = MyColFormHelper()
        self.helper.layout = Layout(
            Div(Div(Field('title', css_class="form-control"), css_class=''),
                Div(Field('document_type', css_class="form-control"), css_class=''),
                Div(Field('rpt_img_file', css_class="form-control"), css_class=''),
                Div(Field('shared_file', css_class="form-control"), css_class=''),css_class = 'col-md-5')
        )


