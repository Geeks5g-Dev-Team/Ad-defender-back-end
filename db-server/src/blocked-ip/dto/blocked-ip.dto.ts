import { PartialType } from '@nestjs/mapped-types';
import {
  IsDate,
  IsNotEmpty,
  IsNumber,
  IsOptional,
  IsString,
} from 'class-validator';

export class CreateBlockedIpDto {
  @IsNotEmpty()
  @IsNumber()
  userId: number;

  @IsNotEmpty()
  @IsString()
  ip: string;

  @IsNotEmpty()
  @IsString()
  reason: string;

  @IsOptional()
  @IsString()
  threatLevel?: string;
}

// Create an update DTO with all fields optional
export class UpdateBlockedIpDto extends PartialType(CreateBlockedIpDto) {
  @IsOptional()
  @IsNumber()
  clicks?: number;

  @IsOptional()
  @IsNumber()
  moneySaved?: number;
}
