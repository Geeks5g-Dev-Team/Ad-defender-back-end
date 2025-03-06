import {
  Body,
  Controller,
  Delete,
  Get,
  Param,
  Patch,
  Post,
} from '@nestjs/common';
import { BlockedIpService } from './blocked-ip.service';
import { CreateBlockedIpDto, UpdateBlockedIpDto } from './dto/blocked-ip.dto';

@Controller('blocked-ips')
export class BlockedIpController {
  constructor(private readonly blockedIpService: BlockedIpService) {}

  @Post()
  create(@Body() data: CreateBlockedIpDto) {
    return this.blockedIpService.create(data);
  }

  @Get()
  findAll() {
    return this.blockedIpService.findAll();
  }

  @Get(':id')
  findOne(@Param('id') id: string) {
    return this.blockedIpService.findOne(parseInt(id));
  }

  @Patch(':id')
  update(@Param('id') id: string, @Body() data: UpdateBlockedIpDto) {
    return this.blockedIpService.update(parseInt(id), data);
  }

  @Delete(':id')
  remove(@Param('id') id: string) {
    return this.blockedIpService.remove(parseInt(id));
  }
}
