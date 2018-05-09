#!/usr/bin/env python

import os
#from kubernetes import client, config, watch
import ssl
import urllib2
import urllib
import subprocess, shlex
import time 
import threading
import time

gcontext = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
ip = subprocess.check_output(shlex.split("gcloud --format='value(networkInterfaces[0].accessConfigs[0].natIP)' compute instances list --filter='name=firewall1'")).rstrip()
api_key = "LUFRPT16Y1BlcXJWSUZrZ3IyQ1BiMXN2d3hSSDhLcUE9eXJiT0ZUdzkyU3I1ZjNIWDhaYzVCTmJaZGhHeFljUWZYQXlQMGViQ1Z6Yz0="
kubernetes.config.load_kube_config(os.path.join(os.environ["HOME"], '.kube/config'))
v1 = kubernetes.client.CoreV1Api()
v1ext = kubernetes.client.ExtensionsV1beta1Api()    


def install_and_import(package):
    import importlib
    try:
        importlib.import_module(package)
    except ImportError:
        import pip
        pip.main(['install', package])
    finally:
        globals()[package] = importlib.import_module(package)




def services():
    FWXMLUpdate = []
    XMLHeader = "<uid-message><version>1.0</version><type>update</type><payload>"
    XMLFooter = "</payload></uid-message>"
    Register = "<register>"

    mysvcs = kubernetes.watch.Watch().stream(v1.list_service_for_all_namespaces)
    for event in mysvcs:
        if event['object'].spec.type == "LoadBalancer":
          Register += '<entry ip="' + event['object'].spec.load_balancer_ip + '">'
        else:
          Register += '<entry ip="' + event['object'].spec.cluster_ip + '">'
        Register += "<tag>"
        for i in event['object'].metadata.labels:
            Register += "<member>" + event['object'].metadata.labels[i] + "</member>"
        Register += "</tag>"
        Register += "</entry>"
        Register += '</register>'
        FWXMLUpdate = XMLHeader + Register + XMLFooter
        url = "https://%s/api/?type=user-id&action=set&key=%s&cmd=%s" % (ip, api_key,urllib.quote(FWXMLUpdate))
        time.sleep(0.5)
        try:
            response = urllib2.urlopen(url,context=gcontext).read()
        except urllib2.HTTPError, e:
           print "HTTPError = " + str(e)


def pods():
    FWXMLUpdate = []
    XMLHeader = "<uid-message><version>1.0</version><type>update</type><payload>"
    XMLFooter = "</payload></uid-message>"
    Register = "<register>"
    mypods = kubernetes.watch.Watch().stream(v1.list_pod_for_all_namespaces)
    for event in mypods:
        Register += '<entry ip="' + event['object'].status.pod_ip + '">'
        Register += "<tag>"
        for i in event['object'].metadata.labels:
            Register += "<member>" + event['object'].metadata.labels[i] + "</member>"
        Register += "</tag>"
        Register += "</entry>"
        Register += '</register>'
        FWXMLUpdate = XMLHeader + Register + XMLFooter
        url = "https://%s/api/?type=user-id&action=set&key=%s&cmd=%s" % (ip, api_key,urllib.quote(FWXMLUpdate))
        time.sleep(0.5)
        try:
            response = urllib2.urlopen(url,context=gcontext).read()
        except urllib2.HTTPError, e:
           print "HTTPError = " + str(e)


def main():
    install_and_import('kubernetes')
    t1 =  threading.Thread(name='watch_pods',target=pods, args=()).start()
    t2 =  threading.Thread(name='watch_svcs',target=services, args=()).start()
    while threading.active_count() > 0:
        time.sleep(1)


if __name__ == '__main__':
    main()