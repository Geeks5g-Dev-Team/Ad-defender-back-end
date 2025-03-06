import { Module } from '@nestjs/common';
import { BlockedIpController } from './blocked-ip.controller';
import { BlockedIpService } from './blocked-ip.service';
import { PrismaService } from 'prisma/prisma.service';

@Module({
  controllers: [BlockedIpController],
  providers: [BlockedIpService, PrismaService],
})
export class BlockedIpModule {}
