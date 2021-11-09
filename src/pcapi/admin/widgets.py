import uuid

import markupsafe
import wtforms.widgets as wtf_widgets
import wtforms.widgets.html5 as wtf_html5_widgets


class AutocompleteSelectWidget(wtf_widgets.Select):
    def __init__(self, endpoint, getter, multiple=False):
        super().__init__(multiple=multiple)
        self.endpoint = endpoint
        self.uuid = uuid.uuid4()
        self.getter = getter

    def __call__(self, field, **kwargs):
        if field.data:
            selected_ids = ",".join(field.data) if self.multiple else field.data
            selected_data = self.getter(field.data if self.multiple else [field.data])
        else:
            selected_ids = ""
            selected_data = []
        if self.multiple:
            selected_data_js = "[%s]" % ",".join('{id: "%(id)s", text: "%(text)s"}' % item for item in selected_data)
        elif selected_data:
            selected_data_js = '{id: "%(id)s", text: "%(text)s"}' % selected_data[0]
        else:
            selected_data_js = "null"
        css_classes = "form-control"
        if field.errors:
            css_classes += " is-invalid"
        html_id = f"{field.name}_{self.uuid}"
        html = f'<input name="{field.name}" id="{html_id}" value="{selected_ids}">'
        html += """
<script>
  document.addEventListener("DOMContentLoaded", function(event) {
    $("#%(html_id)s").select2({
      ajax: {
        url: "%(url)s",
        data: function (term, page) {
          return {
            q: term, // search term
          }
        },
        results: function (data, page) {
            return { results: data.items }
        },
      },
      containerCssClass: "%(css_classes)s",
      initSelection: function (element, callback) {
        selected = %(selected_data)s
        callback(selected)
      },
      minimumInputLength: 3,
      placeholder: "Saisissez quelques lettres…",
    });
  });
</script>
""" % {
            "css_classes": css_classes,
            "html_id": html_id,
            "selected_data": selected_data_js,
            "url": self.endpoint,
        }
        return markupsafe.Markup(html)


class DateInputWithConstraint(wtf_html5_widgets.DateInput):
    def __init__(self, input_type=None, min_date=None, max_date=None):
        super().__init__(input_type=input_type)
        self.min_date = min_date
        self.max_date = max_date

    def __call__(self, field, **kwargs):
        for bound_name, bound in (("min", self.min_date), ("max", self.max_date)):
            if callable(bound):
                bound = bound(field)
            if bound:
                kwargs[bound_name] = bound
        return super().__call__(field, **kwargs)


class SelectWithOptgroups(wtf_widgets.Select):
    def __call__(self, field, **kwargs):
        kwargs.setdefault("id", field.id)
        if self.multiple:
            kwargs["multiple"] = True
        if "required" not in kwargs and "required" in getattr(field, "flags", []):
            kwargs["required"] = True
        if field.size:
            kwargs.setdefault("size", field.size)
        html = ["<select %s>" % wtf_widgets.html_params(name=field.name, **kwargs)]
        for group_label, group_options in field.choices:
            html.append("<optgroup %s>" % wtf_widgets.html_params(label=group_label))
            for value, label in group_options:
                if self.multiple:
                    selected = field.coerce(value) in (field.data or [])
                else:
                    selected = field.coerce(value) == field.data
                html.append(self.render_option(value, label, selected))
            html.append("</optgroup>")
        html.append("</select>")
        return markupsafe.Markup("".join(html))