#!/usr/bin/env python3

import asyncio
from dataclasses import dataclass
import random
import socket
import time

from dns.asyncresolver import Resolver
from dns.nameserver import Do53Nameserver
import dns.rdatatype
import dns.resolver
from httpx import AsyncClient

from dotenv import load_dotenv
load_dotenv()

import config


@dataclass(slots=True)
class Frontend:
    resolver: Resolver
    done: bool = False
    task: asyncio.Task | None = None


class NonRaisingResolver(Resolver):
    async def resolve(self, *args, **kwargs):
        try:
            return await super().resolve(*args, **kwargs)
        except Exception as e:
            return e


class DesecAPIClient(AsyncClient):
    def __init__(self, token: str, *args, **kwargs) -> None:
        super().__init__(
            *args,
            base_url='https://desec.io/api/v1',
            headers={
                'Authorization': f'Token {token}'
            },
            **kwargs,
        )

    async def update_txt_rrset(self, domain: str, subname: str, value: str) -> None:
        resp = await self.put(
            f'/domains/{domain}/rrsets/',
            json=[{
                'subname': subname,
                'type': 'TXT',
                'ttl': 3600,  # this is the minimum TTL supported by deSEC
                'records': [value] if value else [],
            }],
        )
        print(resp.text)
        resp.raise_for_status()


async def main() -> None:
    desec = DesecAPIClient(token=config.DESEC_TOKEN)

    txt_record = f'"{random.randbytes(16).hex()}"'
    print(f'Will set the TXT record to {txt_record}')
    await desec.update_txt_rrset(config.DESEC_DOMAIN, config.DESEC_SUBNAME, txt_record)

    frontends: list[Frontend] = []

    for frontend_host in config.FRONTENDS:
        print(frontend_host[:config.HOSTNAME_DISPLAY_TRIM])

        frontend_addr = next(
            gai[4][0]
            for gai in socket.getaddrinfo(
                frontend_host,
                53,
                family=socket.AF_INET,  # deliberate as my IPv6 at home may not be reliable
                type=socket.SOCK_DGRAM,
                proto=socket.IPPROTO_UDP,
            )
        )

        resolver = NonRaisingResolver()
        resolver.nameservers = (Do53Nameserver(frontend_addr),)
        resolver.lifetime = config.DNS_REQUEST_TIMEOUT
        resolver.timeout = config.DNS_REQUEST_TIMEOUT
        resolver.flags = 0  # do not request recursion

        frontends.append(Frontend(resolver=resolver))

    print(f'\033[{config.HOSTNAME_DISPLAY_TRIM}C', end='')

    qname = config.DESEC_DOMAIN if config.DESEC_SUBNAME == '@' else f'{config.DESEC_SUBNAME}.{config.DESEC_DOMAIN}'

    while not all(frontend.done for frontend in frontends):
        start = time.monotonic()

        try:
            async with asyncio.TaskGroup() as tg:
                for frontend in frontends:
                    if frontend.done:
                        continue

                    frontend.task = tg.create_task(frontend.resolver.resolve(qname, dns.rdatatype.TXT))
        except* Exception:
            pass

        print(f'\033[{len(frontends)}A\033[1C', end='')

        for frontend in frontends:
            if frontend.done:
                print(' ', end='\033[1B\033[1D')
                continue

            assert frontend.task

            result = frontend.task.result()

            if isinstance(result, Exception):
                if isinstance(result, dns.resolver.LifetimeTimeout):
                    symbol, colour = 'T', '41'
                elif isinstance(result, dns.resolver.NoNameservers):
                    symbol, colour = 'R', '41'
                elif isinstance(result, dns.resolver.NXDOMAIN):
                    symbol, colour = 'N', '43'
                else:
                    symbol, colour = '!', '41'
            else:
                if any(str(rr) == txt_record for rr in result.rrset):
                    if len(result.rrset) == 1:
                        frontend.done = True
                        frontend.task = None

                        symbol, colour = 'V', '42'
                    else:
                        symbol, colour = 'M', '43'
                else:
                    symbol, colour = '.', '43'

            print(f'\033[{colour}m{symbol}\033[0m', end='\033[1B\033[1D')

        print('', end='', flush=True)

        delta = time.monotonic() - start

        if delta < config.DNS_REQUEST_TIMEOUT:
            await asyncio.sleep(config.DNS_REQUEST_TIMEOUT - delta)


if __name__ == '__main__':
    asyncio.run(main())
