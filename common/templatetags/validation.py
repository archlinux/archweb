from django import template

register = template.Library()

@register.inclusion_tag('errors.html')
def print_errors(errors):
	errs = []
	for e,msg in errors.iteritems():
		errmsg = str(msg[0])
		# hack -- I'm a python idiot
		errs.append( (e, errmsg[2:-2]) )
	return {'errors': errs}
