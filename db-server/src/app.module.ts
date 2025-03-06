import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { UserModule } from './user/user.module';
import { BlockedIpModule } from './blocked-ip/blocked-ip.module';
import { ClickModule } from './click/click.module';
import { PrismaService } from '../prisma/prisma.service';

@Module({
  imports: [UserModule, BlockedIpModule, ClickModule],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}
