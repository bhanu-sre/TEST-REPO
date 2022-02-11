#!/usr/bin/python

import argparse
import logging
import json
import requests
import os

from requests.exceptions import ConnectionError

requests.packages.urllib3.disable_warnings()

exit_codes = {
    'OK': 0,
    'WARNING': 1,
    'CRITICAL': 2,
    'UNKNOWN': 3
}


def nagios_exit(status, msg, perfdata=None):
    if status == 'OK':
        print '{0} - {1} | {2}'.format(status, msg, perfdata)
        os.sys.exit(exit_codes[status])

    if status == 'WARNING':
        print '{0} - {1} | {2}'.format(status, msg, perfdata)
        os.sys.exit(exit_codes[status])

    if status == 'CRITICAL':
        print '{0} - {1} | {2}'.format(status, msg, perfdata)
        os.sys.exit(exit_codes[status])

    if status == 'UNKNOWN':
        print '{0} - {1} | {2}'.format(status, msg, perfdata)
        os.sys.exit(exit_codes[status])


def json_dump(i):
    """
    pretty.
    """

    return json.dumps(i, indent=2, sort_keys=True)


def logger(log_file=None, level='WARN'):
    """

    Basic logger - used when debugggin, not for Nagios / Icinga Output
    """

    level = logging.getLevelName(level)
    logger = logging.getLogger()
    logger.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', '%Y-%m-%d %H:%M:%S')

    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    else:
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    return logger


def get_args():
    """

    Get user input.
    """

    parser = argparse.ArgumentParser(usage=__doc__)

    parser.add_argument('--ns-host',
                        help='NetScaler HostName / IP - nitro Api',
                        required=False)
    parser.add_argument('--ns-port',
                        help='Enter port',
                        default=80,
                        required=False)
    parser.add_argument('--key',
                        help='Nitro Api Path, ex /ns for basic ns stats',
                        required=True)
    parser.add_argument('--value',
                        help='Maps to one level down, metric to alert on',
                        required=True)
    parser.add_argument('--warn',
                        help='Warning Threshold',
                        required=True)
    parser.add_argument('--crit',
                        help='Critical Threshold',
                        required=True)
    parser.add_argument('--debug',
                        help='logging output to stdout or file with --file',
                        required=False,
                        default=False)
    parser.add_argument('--debug-level',
                        help='logging level',
                        required=False,
                        default=False)
    parser.add_argument('--log-out',
                        help='Specify logging output file',
                        required=False)
    parser.add_argument('--json-file',
                        help='Use json input rather than livec query',
                        required=False)
    parser.add_argument('--ns-user',
                        help='Nitro Api User',
                        required=False)
    parser.add_argument('--ns-passwd',
                        help='Nitro Api Password',
                        required=False)

    return parser



def check_run(args, log):
    """

    Put something useful here.

    """

    user = args.ns_user
    passwd = "M@njesh1nine8nine"

    if args.json_file is not None:
        with open(args.json_file) as json_file:
            j_data = json.load(json_file)
    elif 'bucket_bandwidth' in args.value:
        try:
            url = 'https://{0}.softlayer.local/nitro/v1/stat/{1}/{2}?statbindings=yes'.format(args.ns_host, args.key, args.value)
            req = requests.get(url, verify=False, auth=(user, passwd))
            req.raise_for_status()
            j_data = req.json()
            if args.debug == 'True':
                print 'Full Response from API \n:'
                print json_dump(j_data)
        except requests.exceptions.RequestException as ee:
            nagios_exit('OK', ' {0}'.format(ee),'unableToConnect=1 success=0')
    else:

        try:
            url = 'https://{0}.softlayer.local/nitro/v1/stat/{1}/'.format(args.ns_host, args.key)
            req = requests.get(url, verify=False, auth=(user, passwd))
            req.raise_for_status()
            j_data = req.json()
            if args.debug == 'True':
                print 'Full Response from API \n:'
                print json_dump(j_data)
#        except requests.exceptions.HTTPError as ee:
#            raise SystemExit(ee)
#        except ConnectionError as e:
        except requests.exceptions.RequestException as ee:
            nagios_exit('UNKNOWN', ' {0}'.format(ee),'unableToConnect=1 success=0')

    ## Future stuff.
    vals = args.key.split('.')
    numVals = len(vals)
    valsL = [[i] for i in vals]

    ## Onto checks

    warn = int(args.warn)
    crit = int(args.crit)

    metric_path = [args.key, args.value]

    # Stream Identifier Checks
    if 'bucket_bandwidth' in args.value:
      if "streamsession" in j_data["streamidentifier"][0]:
        sorted_j_data = sorted(j_data["streamidentifier"][0]["streamsession"], key=lambda i: int(i["streamobjbandw"]), reverse=True)
        top_ten = sorted_j_data[:10]
        pre_perf_data = []
        for x in range(len(top_ten)):
            pre_perf_data.append(top_ten[x]["name"] + '_Bandw' + '=' + top_ten[x]["streamobjbandw"])
            pre_perf_data.append(top_ten[x]["name"] + '_Req' + '=' + top_ten[x]["streamobjreq"])
            pre_perf_data.append(top_ten[x]["name"] + '_Resptime' + '=' + top_ten[x]["streamobjresptime"])
            pre_perf_data.append(top_ten[x]["name"] + '_Conn' + '=' + top_ten[x]["streamobjconn"])
            pre_perf_data.append(top_ten[x]["name"] + '_BreachCnt' + '=' + top_ten[x]["streamobjbreachcnt"])
            pre_perf_data.append(top_ten[x]["name"] + '_PktCredits' + '=' + top_ten[x]["streamobjpktcredits"])
            pre_perf_data.append(top_ten[x]["name"] + '_PktPerSec' + '=' + top_ten[x]["streamobjpktspersecond"])
            pre_perf_data.append(top_ten[x]["name"] + '_DroppedConns' + '=' + top_ten[x]["streamobjdroppedconns"])
        perf_data = ' '.join(pre_perf_data)
        nagios_exit('OK','{0} - stream identifier metrics'.format(args.value),eval(json.dumps(perf_data)))
      else:
        nagios_exit('OK','{0} - No stream identifier metrics'.format(args.value))


    # interface check
    if args.key == 'interface':
        interfaces = j_data['Interface']

        healthy_ints, warn_ints, crit_ints, unhealthy_ints = [], [], [], []

        if args.value == 'rxbytesrate' or args.value == 'txbytesrate':
            # We only care about LA/LO interfacesi for now...ignore all others...
            for interface in interfaces:
                if 'LA' in interface['id']:
                    if args.debug == 'True':
                        print 'Interface current value'.format(interface['id'], interface[args.value])

                    if (interface[args.value] <= warn and interface[args.value] > 0):
                        int_stat = interface['id'] + ' ' + str(interface[args.value])
                        healthy_ints.append(int_stat)
                    elif interface[args.value] >= warn and interface[args.value] < crit:
                        int_stat = interface['id'] + ' ' + str(interface[args.value])
                        warn_ints.append(int_stat)
                    elif (interface[args.value] >= crit or interface[args.value] == 0):
                        int_stat = interface['id'] + ' ' + str(interface[args.value])
                        crit_ints.append(int_stat)
                    else:
                        int_stat = interface['id'] + ' ' + str(interface[args.value])
                        unhealthy_ints.append(int_stat)
            if len(unhealthy_ints) == 0 and len(healthy_ints) > 0 and len(warn_ints) == 0 and len(crit_ints) == 0:
                nagios_exit('OK',
                            'LA interfaces {0} OK : {1} '.format(args.value, ', '.join(healthy_ints))
                            )
            elif len(warn_ints) > 0:
               nagios_exit('WARNING',
                           'LA Interfaces {0} WARNING - {1} '.format(args.value, ' '.join(warn_ints))
                           )
            elif len(crit_ints) > 0:
               nagios_exit('CRITICAL',
                           ' LA Interfaces {0} CRITICAL: - {1} '.format(args.value, ' '.join(crit_ints))
                           )
            else:
               nagios_exit('UKNOWN',
                           'Unable to obtain Interface bytes rate!'
                          )
        elif args.value == 'curintfstate':
            # We only care about LA/LO interfacesi for now...ignore all others... 
            for interface in interfaces:
                if 'LA' in interface['id'] or 'LO' in interface['id']:
                    if args.debug == 'True':
                        print 'Interface current state: {0} - {1}'.format(interface['id'], interface['curintfstate'])
    
                    if interface['curintfstate'] == 'UP':
                        int_stat = interface['id'] + ' ' + interface['curintfstate']
                        healthy_ints.append(int_stat)
                    else:
                        int_stat = interface['id'] + ' ' + interface['curintfstate'] 
                        unhealthy_ints.append(int_stat)
    
            if len(unhealthy_ints) == 0 and len(healthy_ints) > 0:
                nagios_exit('OK',
                            'All LO/LA interfaces found are UP: {0} '.format(', '.join(healthy_ints))
                            )
    
            elif len(unhealthy_ints) > 0:
                nagios_exit('CRITICAL',
                            ' LO/LA Interfaces found not UP: - {0} '.format(' '.join(unhealthy_ints))
                            )
            else:
                nagios_exit('UKNOWN',
                            'Unable to obtain interface status!'
                           )
        else:
            print '--value is missing or incorrect for --key interface'

    # lb vserver 
    # actsvcs check
    if args.key == 'lbvserver':
        targetLBVserver = None 
        for vserver in j_data[args.key]:
            if args.debug == 'True':
                print json_dump(vserver)
            if args.value == vserver['name']:
                targetLBVserver = vserver
        if targetLBVserver is None:
            nagios_exit('UNKNOWN', 'Unable to Fetch metric: {0} from json output'.format(' '.join(metric_path)),
                        'metricNotFoundinApi=1'
                        )
        try: 
            metric_val = int(targetLBVserver['actsvcs'])
        except Exception as e:
            nagios_exit('UNKNOWN', 'Unable to Fetch metric: {0} from json output: {1}'.format(' '.join(metric_path), e),
                        'metricNotFoundinApi=1'
                        )
            if args.debug == 'True':
                print 'Target LB Vserver: \n', targetLBVserver
        if metric_val <= crit:
            nagios_exit('CRITICAL',
                        '{0} - {1} Active Services are lower than/equals to supplied critical threshold of {2}'.format(args.value,
                                                                                             metric_val,
                                                                                             crit),
                                                                                             '{0}={1} success=0'.format(
                                                                                                 args.value + '_ActiveServices', metric_val)
                        )

#        if metric_val <= warn:
#            nagios_exit('WARNING',
#                        '{0} - {1} Active Services are lower than/equals to supplied warning threshold of {2}'.format(args.value,
#                                                                                            metric_val,
#                                                                                            warn),
#                                                                                            '{0}={1} success=0'.format(
#                                                                                                args.value + '_ActiveServices', metric_val)
#                       )

        if metric_val > crit:
            nagios_exit('OK',
                        '{0} - {1} Active Services are above supplied warning threshold of {2}'.format(args.value,
                                                                                      metric_val,
                                                                                      warn),
                                                                                      '{0}={1} success=1'.format(
                                                                                          args.value + '_ActiveServices', metric_val
                                                                                      )
                        )

    # RX / TX Checks
    if 'bitsrate' in args.value:

        if 'tx' in args.value:
            extra_perf = 'tottxmbits'
        if 'rx' in args.value:
            extra_perf = 'totrxmbits'

        try:
            metric_val = j_data[args.key][args.value]
            perf_val = j_data[args.key][extra_perf]

        except Exception as e:
            nagios_exit('UNKNOWN', 'Unable to Fetch metric: {0} from json output: {1}'.format(' '.join(metric_path), e),
                        'metricNotFoundinApi=1'
                        )

        if metric_val >= crit:
            nagios_exit('CRITICAL',
                        '{0} - {1} is higher than supplied threshold of {2}'.format(args.value,
                                                                                    metric_val,
                                                                                    crit),
                                                                                    '{0}={1} {2}={3} success=0'.format(args.value, metric_val, extra_perf, perf_val)
                        )
        if metric_val >= warn:
            nagios_exit('WARNING',
                        '{0} - {1} is higher than supplied threshold of {2}'.format(args.value,
                                                                                    metric_val,
                                                                                    warn),
                                                                                    '{0}={1} {2}={3} success=0'.format(args.value, metric_val, extra_perf, perf_val)
                        )

        if metric_val < warn:
            nagios_exit('OK',
                        '{0} - {1} is below supplied critial threshold of {2}'.format(args.value,
                                                                                      metric_val,
                                                                                      crit),
                                                                                      '{0}={1} {2}={3} success=1'.format(args.value, metric_val, extra_perf, perf_val)
                         )

    # Cpu related checks - pct usage & pkt pct usage
    # Anything fetched from nitro/v1/stat/system, really

    if args.key == 'system':
        try:
            metric_val = j_data[args.key][args.value]

        except Exception as e:
            nagios_exit('UNKNOWN', 'Unable to Fetch metric: {0} from json output: {1}'.format(' '.join(metric_path), e),
                        'metricNotFoundinApi=1'
                        )

        if metric_val >= crit:
            nagios_exit('CRITICAL',
                        '{0} - {1} is higher than supplied critical threshold of {2}'.format(args.value,
                                                                                             metric_val,
                                                                                             crit),
                                                                                             '{0}={1} success=0'.format(
                                                                                                 args.value, metric_val)
                        )
        if metric_val >= warn:
            nagios_exit('WARNING',
                        '{0} - {1} is higher than supplied warning threshold of {2}'.format(args.value,
                                                                                            metric_val,
                                                                                            warn),
                                                                                            '{0}={1} success=0'.format(
                                                                                                args.value, metric_val)
                        )

        if metric_val < warn:
            nagios_exit('OK',
                        '{0} - {1} is below supplied warning threshold of {2}'.format(args.value,
                                                                                      metric_val,
                                                                                      warn),
                                                                                      '{0}={1} success=1'.format(
                                                                                          args.value, metric_val
                                                                                      )
                        )

    if args.key == 'clusternode':
        inactive, unhealthy, healthy, ipHostnameMap = [], [], [], []

        for nodeBlob in j_data['clusternode']:
            if nodeBlob['clnodeeffectivehealth'] == 'UP':
                nodeState = {
                    'IP': nodeBlob['clnodeip'],
                    'State': nodeBlob['clnodeeffectivehealth']
                }
                healthy.append(dict(nodeState))

            if nodeBlob['clnodeeffectivehealth'] != 'UP':
                nodeState = {
                    'IP': nodeBlob['clnodeip'],
                    'State': nodeBlob['clnodeeffectivehealth']
                }
                unhealthy.append(dict(nodeState))

        nodes = []
        if len(unhealthy) == 0:
            for node in healthy:
                nodes.append(node['IP'])

            nagios_exit('OK',
                        'All NS Nodes in Cluster Healthy: {0}'.format(', '.join(nodes))
                        )

        if len(unhealthy) > 0:
            for node in unhealthy:
                nodes.append(node['IP'])

            nagios_exit('CRITICAL',
                        'Unhealthy NS Nodes in Cluster {0} Found: {1}'.format(args.ns_host, ' '.join(nodes))
                        )

    ## Execution SHOULD NOT get this far - if it has, then the supplied --key input is invalid - exit UNKNOWN
    nagios_exit('UNKNOWN', 'Invalid check --key supplied!')

    return True


def main():

    args = get_args().parse_args()

    if args.debug_level is False:
        if args.log_out is False:
            log = logger()
        else:
            log = logger(log_file=args.log_out)
    else:
        if args.log_out is False:
            log = logger(level=str.upper(args.debug_level))
        else:
            log = logger(level=str.upper(args.debug_level), log_file=args.log_out)

    if args.__dict__.values()[0] is None:
        log.warning(get_args().print_help())
        os.sys.exit(1)

    check_result = check_run(args, log)

    # sanity
    assert check_result


if __name__ == '__main__':
    main()
