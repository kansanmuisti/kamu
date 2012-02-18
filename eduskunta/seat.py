# -*- coding: utf-8 -*-
import re
import os
import logging
from lxml import etree, html
from eduskunta.importer import Importer
from parliament.models.member import Seat, MemberSeat, Member

class SeatImporter(Importer):
    SEAT_FILENAME = 'seats.txt'
    MPSEAT_FILENAME = 'mp-seats.txt'

    def import_seats(self):
        path = os.path.dirname(os.path.realpath(__file__))
        f = open(os.path.join(path, self.SEAT_FILENAME))
        count = 0
        for line in f.readlines():
            line = line.decode('utf8').strip()
            if not line or line[0] == '#':
                continue
            (row, seat, x, y) = line.split('\t')
            try:
                seat = Seat.objects.get(row=row, seat=seat)
                if not self.replace:
                    continue
            except Seat.DoesNotExist:
                seat = Seat(row=row, seat=seat)
            seat.x = x
            seat.y = y
            seat.save()
            count += 1
        self.logger.info(u"%d seat coordinates imported" % count)
        f.close()

        count = 0
        f = open(os.path.join(path, self.MPSEAT_FILENAME))
        for line in f.readlines():
            line = line.decode('utf8').strip()
            if not line or line[0] == '#':
                continue
            (row, seat, mp, begin, end) = line.split('\t')
            if end == '-':
                end = None
            mp = Member.objects.get(name=mp)
            try:
                mps = MemberSeat.objects.get(member=mp, begin=begin)
                if not self.replace:
                    continue
            except MemberSeat.DoesNotExist:
                mps = MemberSeat(member=mp, begin=begin)
            seat = Seat.objects.get(row=row, seat=seat)
            mps.seat = seat
            mps.end = end
            mps.save()
            count += 1
        self.logger.info(u"%d MP seatings imported" % count)
        f.close()
