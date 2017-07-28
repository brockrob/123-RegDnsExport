from splinter import Browser
import time
import sys
import dns.resolver

def exportZone(domain, browser):
    zone = []
    browser.visit("https://www.123-reg.co.uk/secure/cpanel/manage-dns?domain=" + domain)
    browser.click_link_by_id('advanced-tab')
    a = 0
    while browser.is_element_present_by_id('dns_entry_0') == False:
        time.sleep(1)
        a += 1
        if a == 5:  # Jeez, this is taking a while to load
            if browser.is_element_present_by_id('dns_entry_0') == False and browser.is_element_present_by_id('new-footer') == True:
                print("No Records for {}, but page has already loaded".format(domain))
                return "lookupFailed"
    table = browser.find_by_xpath("//*[contains(@id, 'dns_entry_')]")
    for row in table:
        hostdict = {}
        cells = row.find_by_css('td')
        if cells[4].text.endswith('...'):  # sometimes long things get truncated by their UI
            target = cells[4].html.split('title="')[1].split('"')[0]  # fortunately it's here in a title field
        else:
            target = cells[4].text
        hostname = cells[0].text
        hostdict['hostname'] = hostname
        if cells[1].text == 'TXT/SPF':  # come on 123-reg, this isn't a real record type
            hostdict['type'] = 'TXT'
            hostdict['dest'] = '"{}"'.format(target)  # and TXT records need quotes
        else:
            hostdict['type'] = cells[1].text
            hostdict['dest'] = target
        hostdict['priority'] = cells[2].text
        hostdict['ttl'] = cells[3].text
        zone.append(hostdict)
    return zone

def login(browser):
    browser.visit("https://www.123-reg.co.uk/secure")
    browser.fill('username', inputUsername)
    browser.fill('password', inputPassword)
    browser.find_by_id('login').first.click()
    while browser.is_element_visible_by_xpath('//*[@id="body"]/div/div[5]/div[3]/div/table/tbody/tr/td[3]/input') == False:
        time.sleep(1)
    return browser


def enumDomains(browser):
    url = "https://www.123-reg.co.uk/secure/cpanel/domain/view_domains?rows=1000"
    browser.visit(url)
    table = browser.find_by_id('domstable').text.split('\n')[1:]
    domlist = []
    for row in table:
        domlist.append(row.split(' ')[0])
    return domlist


def tabulate(rows_of_columns):
    num_columns = len(max(rows_of_columns, key=len))
    # I pinched this function from one of my other projects. It only works if all rows are have equal number of items
    # Here follows a dirty hack to pad the first two ($ORIGIN and $TTL) out to the right length
    for row in rows_of_columns:
        while len(row) != num_columns:
            row.append('')
    columns_of_rows = list(zip(*rows_of_columns))
    try:
        column_widths = [max(map(len, column)) for column in columns_of_rows]
    except TypeError:  # Sometimes column contains an int
        column_widths = [max(map(len, str(column))) for column in columns_of_rows]
    column_specs = ('{{:{w}}}'.format(w=max(width, 1)) for width in column_widths)
    format_spec = ' '.join(column_specs)
    table = ''
    for row in rows_of_columns:
        table += format_spec.format(*row) + '\n'
    return table


def formatZone(domain, zone, defTTL):
    table = []
    table.append(['$ORIGIN {}.'.format(domain)])
    if defTTL:
        table.append(['$TTL {}'.format(defTTL)])
    for record in zone:
        table.append([record['hostname'], record['ttl'], 'IN', record['type'], record['priority'], record['dest']])
    formattedTable = tabulate(table)
    return formattedTable


def writeZone(domain, zonef):
    with open(domain + '.zone', 'w') as f:
        f.write(zonef)


def getNameServerRecord(domain):
    try:
        answers = dns.resolver.query(domain, 'NS')
    except (dns.resolver.NoNameservers, dns.resolver.NXDOMAIN):
        print('Domain {} has no nameservers!'.format(domain))
        return 'none'
    return answers[0].target


def defaultTTL(zone, NSrecord, domain):
    res = dns.resolver.Resolver()
    answer = res.query(NSrecord)
    res.nameservers = [str(answer.rrset.items[0])]
    try:
        for record in zone:
            if record['ttl'] == '':
                host = record['hostname']
                if host == '@':
                    query = domain
                else:
                    query = host + '.' + domain
                answer = res.query(query)
                return answer.rrset.ttl
    except:
        print('No Answer found for {}'.format(domain))
        return
    return False


def processDomain(domain, browser):
    NSrecord = str(getNameServerRecord(domain))
    if not NSrecord.endswith('123-reg.co.uk.') or NSrecord.endswith('hosteurope.com.'):  # Sometimes they're only the registrar and DNS is elsewhere
        print("123-Reg does not appear to be the DNS provider for {}.".format(domain))
        return
    zone = exportZone(domain, browser)
    if zone == "lookupFailed":
        return
    defTTL = defaultTTL(zone, NSrecord, domain)  # Try to figure out the domain's default TTL
    zonef = formatZone(domain, zone, defTTL)
    print(zonef)
    writeZone(domain, zonef)


if __name__ == "__main__":
    with Browser("firefox") as browser:
        inputUsername = sys.argv[2]
        inputPassword = sys.argv[3]
        browser = login(browser)
        if sys.argv[1] != 'all':
            domain = sys.argv[1]
            processDomain(domain, browser)
        if sys.argv[1] == 'all':
            domlist = enumDomains(browser)
            for domain in domlist:
                processDomain(domain, browser)
