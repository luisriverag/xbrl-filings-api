{{ fullname[17:] | escape | underline}}

.. currentmodule:: {{ module }}

.. autoclass:: {{ objname }}
   {%- block methods %}{% if methods %}

   .. rubric:: {{ _('Methods') }}

   .. autosummary::
   {%- set summary_meths = sort_dunders_last(methods) %}
   {% for item in summary_meths %}
      ~{{ name }}.{{ item }}
   {%- endfor %}
   {%- endif %}{% endblock %}
   {%- block attributes %}{% if attributes %}

   .. rubric:: {{ _('Attributes') }}

   .. autosummary::
   {%- set summary_attrs = sort_dunders_last(attributes) %}
   {% for item in summary_attrs if not item|upper == item and item|lower in attributes %}
      ~{{ name }}.{{ item }}
   {%- endfor %}
   {%- endif %}{% endblock %}
