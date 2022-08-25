from flask import Flask, render_template

app = Flask(__name__)

import subprocess

def escape(s):
    # strings have crap like \032 that we need to escape and convert to ascii
    state = 0 # 0 = normal, 1-3 = escaping
    esc = []
    out = []

    for c in s:
        if state == 0:
            if c == '\\':
               state = 1
               continue
            else: 
                out.append(c)
        elif state == 1:
            if c == '\\':  # \\ means \
                out.append('\\')
                state = 0
            elif c.isnumeric():  # 1st digit
                esc.append(c)
                state = 2
        elif state == 2:
            if c.isnumeric():  # 2nd digit
                esc.append(c)
                state = 3
        elif state == 3:
            if c.isnumeric():  # 3rd digit, done!
                esc.append(c)
                out.append(chr(int(''.join(esc))))
                esc = []
                state = 0

    return ''.join(out)

def get_avahi_output(protocol):
    services = []
    ret = subprocess.run(("avahi-browse", "-cpr", f"_{protocol}._tcp"), capture_output=True, encoding='ascii')
    for line in ret.stdout.split('\n'):
        if line:
            line = line.split(';')
            if line[0] != '=':  # = indicates dns resolution succeeded, see avahi-browse man page
                continue
            if line[1] == 'lo':  # services on loopback will also be found on IPv4, don't duplicate them
                continue
            if line[2] != 'IPv4':
                continue

            desc = escape(line[3])
            host = line[6]
            port = line[8]

            services.append({"desc": desc, "uri": f"{protocol}://{host}:{port}"})
    return services


@app.route('/')
def index():
    zc_services = []
    zc_services += get_avahi_output("http")
    zc_services += get_avahi_output("https")
    zc_services.sort(key=(lambda d: d["desc"]))

    #return services
    # TODO static services imported from file
    return render_template('zeroconf_dir.html', zeroconf_services=zc_services, static_services=[])
