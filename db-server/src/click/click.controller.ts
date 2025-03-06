import {
  Body,
  Controller,
  Delete,
  Get,
  Param,
  Patch,
  Post,
} from '@nestjs/common';
import { ClickService } from './click.service';
import { CreateClickDto, UpdateClickDto } from './dto/click.dto';

@Controller('clicks')
export class ClickController {
  constructor(private readonly clickService: ClickService) {}

  @Post()
  create(@Body() data: CreateClickDto) {
    return this.clickService.create(data);
  }

  @Get()
  findAll() {
    return this.clickService.findAll();
  }

  @Get(':id')
  findOne(@Param('id') id: string) {
    return this.clickService.findOne(parseInt(id));
  }

  @Patch(':id')
  update(@Param('id') id: string, @Body() data: UpdateClickDto) {
    return this.clickService.update(parseInt(id), data);
  }

  @Delete(':id')
  remove(@Param('id') id: string) {
    return this.clickService.remove(parseInt(id));
  }

  @Patch('/mark-fraudulent/:ip')
  async markClicksAsFraudulent(@Body() updateDto: { ip: string }) {
    return this.clickService.markClicksAsFraudulent(updateDto.ip);
  }
}
