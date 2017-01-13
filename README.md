# 123-RegDnsExport
Export DNS zones from 123-reg.co.uk to BIND compliant zone files for use with real DNS providers

Depends on Splinter and Firefox.

I once had to migrate a bunch of DNS from 123-reg to AWS. Much to my dismay, 123-Reg do not seem to have any sort of API, and provide no way of exporting zone files. I opened a ticket to see if their support department could dump zone files for me, but they refused. So, I made this thing.

It logs in to their site, scrapes the DNS records from their web portal, and writes it out to nice zone files that can then be imported to real DNS providers like AWS' Rout53 offering.

Usage:

123-RegDnsExport.py domain|all username password

In the first argument, either a particular domain or 'all' can be used. If a domain is specified, that domain's DNS records will be exported; if 'all' is used, all domains in the specified account will be exported.

Domains will not be exported if 123-reg is not the DNS provider for the domain (ns*.123-reg.co.uk is not an NS record.)
