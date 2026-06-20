import os
Q = chr(34)
q = chr(39)

lines = []

# Helper
def a(s): lines.append(s)

# Header
a("{% extends " + Q + "base.html" + Q + " %}")
a("{% load direccion_extras permissions_tags %}")
a("{% load thumbnail %}")
a("{% block title %}{{ carpeta.nombre }} - Bienes{% endblock %}")
a("{% block page_title %}{{ carpeta.nombre }}{% endblock %}")
a("{% block page_actions %}")
a("<div class=" + Q + "flex gap-3" + Q + ">")
a("{% if can:" + Q + "bienes_editar" + Q + " %}")
a("<a href=" + Q + "#" + Q + " class=" + Q + "px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white rounded-lg transition-all" + Q + "><i class=" + Q + "fas fa-edit mr-2" + Q + "></i>Editar</a>")
a("{% endif %}")
a("{% if can:" + Q + "bienes_eliminar" + Q + " %}")
a("<form method=" + Q + "post" + Q + " action=" + Q + "{% url " + q + "bien_carpeta_eliminar" + q + " carpeta.pk %}" + Q + " class=" + Q + "inline" + Q + " onsubmit=" + Q + "return confirm(" + q + "Eliminar esta carpeta?" + q + ")" + Q + ">{% csrf_token %}")
a("<button type=" + Q + "submit" + Q + " class=" + Q + "px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg transition-all" + Q + "><i class=" + Q + "fas fa-trash mr-2" + Q + "></i>Eliminar</button>")
a("</form>")
a("{% endif %}")
a("</div>")
a("{% endblock %}")
a("{% block content %}")
a("<div class=" + Q + "space-y-6" + Q + ">")

# Navbar / Breadcrumbs
a("<nav class=" + Q + "text-sm text-gray-400 mb-4" + Q + ">")
a("<a href=" + Q + "{% url " + q + "bien_list" + q + " %}" + Q + " class=" + Q + "hover:text-white transition-colors" + Q + ">Bienes</a>")
a("{% for crumb in breadcrumbs %}")
a("<span class=" + Q + "mx-2" + Q + ">/</span>")
a("<a href=" + Q + "{% url " + q + "bien_carpeta_detail" + q + " crumb.pk %}" + Q + " class=" + Q + "hover:text-white transition-colors" + Q + ">{{ crumb.nombre }}</a>")
a("{% endfor %}")
a("<span class=" + Q + "mx-2" + Q + ">/</span>")
a("<span class=" + Q + "text-white" + Q + ">{{ carpeta.nombre }}</span>")
a("</nav>")

with open("/DATA/CIM5NV/templates/direccion/bien_carpeta_detail.html", "w") as f:
    f.write("\n".join(lines))
    f.write("\n")
print("Template generated: " + str(len(lines)) + " lines")
