import { Injectable } from '@nestjs/common';
import { PrismaService } from 'prisma/prisma.service';
import { CreateClickDto, UpdateClickDto } from './dto/click.dto';
import { Prisma } from '@prisma/client';

@Injectable()
export class ClickService {
  constructor(private prisma: PrismaService) {}

  async create(data: CreateClickDto) {
    return this.prisma.click.create({ data });
  }

  async findAll() {
    return this.prisma.click.findMany();
  }

  async findOne(id: number) {
    return this.prisma.click.findUnique({ where: { id } });
  }

  async update(id: number, data: UpdateClickDto) {
    return this.prisma.click.update({ where: { id }, data });
  }

  async remove(id: number) {
    return this.prisma.click.delete({ where: { id } });
  }

  async updateMany(
    where: Prisma.ClickWhereInput,
    data: Prisma.ClickUpdateInput,
  ) {
    return this.prisma.click.updateMany({
      where,
      data,
    });
  }

  async markClicksAsFraudulent(ip: string) {
    try {
      const updateResult = await this.prisma.click.updateMany({
        where: { ip: ip }, // ✅ Explicitly reference the ip field
        data: { isFraudulent: true },
      });

      return {
        message: `✅ Updated ${updateResult.count} clicks as fraudulent for IP: ${ip}`,
      };
    } catch (error) {
      console.error(`❌ Error updating fraudulent clicks: ${error.message}`);
      throw new Error(`Failed to mark clicks as fraudulent for IP: ${ip}`);
    }
  }
}
