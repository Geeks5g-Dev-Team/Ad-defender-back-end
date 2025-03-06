import { Injectable } from '@nestjs/common';
import { PrismaService } from 'prisma/prisma.service';
import { CreateBlockedIpDto, UpdateBlockedIpDto } from './dto/blocked-ip.dto';

@Injectable()
export class BlockedIpService {
  constructor(private prisma: PrismaService) {}

  async create(data: CreateBlockedIpDto) {
    return this.prisma.blockedIp.create({ data });
  }

  async findAll() {
    return this.prisma.blockedIp.findMany();
  }

  async findOne(id: number) {
    return this.prisma.blockedIp.findUnique({ where: { id } });
  }

  async update(id: number, data: UpdateBlockedIpDto) {
    return this.prisma.blockedIp.update({ where: { id }, data });
  }

  async remove(id: number) {
    return this.prisma.blockedIp.delete({ where: { id } });
  }
}
