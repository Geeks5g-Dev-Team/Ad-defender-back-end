import { Module } from '@nestjs/common';
import { ClickController } from './click.controller';
import { ClickService } from './click.service';
import { PrismaService } from 'prisma/prisma.service';

@Module({
  controllers: [ClickController],
  providers: [ClickService, PrismaService],
})
export class ClickModule {}
