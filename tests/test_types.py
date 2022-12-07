def test_types():
    # not much to do here except make sure they can be imported and used
    import bento_lib.types as bt

    service_type: bt.GA4GHServiceType = {
        "group": "ca.c3g.bento",
        "artifact": "service-registry",
        "version": "1.0.0",
    }

    service_org: bt.GA4GHServiceOrganization = {
        "name": "C3G",
        "url": "http://www.computationalgenomics.ca"
    }

    service_info_dict: bt.GA4GHServiceInfo = {
        "id": "1",
        "name": "Bento Service Registry",
        "type": service_type,
        "description": "Service registry for a Bento platform node.",
        "organization": service_org,
        "contactUrl": "mailto:david.lougheed@mail.mcgill.ca",
        "version": "1.0.0",
        "url": "https://service-registry.example.org",
        "environment": "prod"
    }

    print(service_info_dict)
