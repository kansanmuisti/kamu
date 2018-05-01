
import sys
import urls
import inspect
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import subprocess
import os

def resource_api_string(resource, output):
	docitems = []
	path = resource.get_resource_uri()
	path_name = path.split('/')[-2]
	pk = None
	if hasattr(resource.Meta, "object_class"):
		cls = resource.Meta.object_class
		api_name = cls.__name__
	else:
		return # Skip "fake" resources.
		#api_name = path_name.capitalize()
	
	detail_uri_name = getattr(resource, 'detail_uri_name', 'id')
	schema = resource.build_schema()

	common_params = []
	custom_params = getattr(resource.Meta, 'custom_parameters', {})
	for param, spec in custom_params.items():
		common_params.append("@apiParam {%s} %s %s\n"%(
			spec['type'], param, spec['descr']))
	
	common_params = "".join(common_params)
	
	output.write('"""\n')
	output.write("@api {get} %s %s\n"%(path+":%s/"%detail_uri_name, api_name))
	output.write("@apiName %s\n"%(api_name))
	output.write("@apiVersion 1.0.0\n") # Apidocjs doesn't like it without this
	output.write("@apiGroup %s\n\n"%(api_name))
	
	docstring = inspect.getdoc(resource.__class__)
	if docstring is None:
		docstring = inspect.getdoc(resource.Meta.object_class)
		# Hackly remove automatic crappy docstrings done by django.
		if docstring.startswith("%s(id,"%api_name):
			docstring = None

	if docstring is not None:
		output.write("@apiDescription %s\n"%docstring)
	output.write(common_params)
	
	for field_name, field in schema['fields'].items():
		field.update(dict(name=field_name))
		output.write("@apiSuccess {%(type)s} %(name)s %(help_text)s\n"%field)
	output.write('"""\n')
	output.write('"""\n')
	output.write("@api {get} %s %s listing\n"%(path, api_name))
	output.write("@apiName %s_list\n"%(api_name))
	output.write("@apiVersion 1.0.0\n") # Apidocjs doesn't like it without this
	output.write("@apiGroup %s\n\n"%(api_name))
	
	output.write(common_params)
	for filt in getattr(resource.Meta, 'filtering', {}):
		filt_field = schema['fields'][filt]
		output.write("@apiParam {%s} %s Filter by %s\n"%(
			filt_field['type'], filt, filt))
	
	if hasattr(resource.Meta, 'ordering'):
		fields = resource.Meta.ordering
		fields = ', '.join("'%s'"%f for f in fields)
		output.write("@apiParam {string} order_by Order by field. Supports: %s\n"%(fields))
		
	
	output.write("@apiSuccess {object} meta Information about the query itself\n")
	output.write("@apiSuccess {%s[]} objects Matching %s objects\n"%(api_name, api_name))
	output.write('"""\n\n')

def build_api_docs(api, output=sys.stdout):
	for resource in api._registry.values():
		resource_api_string(resource, output)

class Command(BaseCommand):
	help = "Build Kamu REST API documentation."

	def handle(self, *args, **options):
		# Better run from the project root!
		hackfile_path = "Docs/hackily_generated_tmp_docs.py"
		hackfile = open(hackfile_path, 'w')
		dst_dir = os.path.join(settings.STATIC_ROOT, 'api_v1_doc')
		build_api_docs(urls.v1_api, hackfile)
		hackfile.close()
		subprocess.call([
			"apidoc", "-i", "Docs", 
			"-f", "^hackily_generated_tmp_docs.py$",
			"-f", "^package.json$",
			"-o", dst_dir])

