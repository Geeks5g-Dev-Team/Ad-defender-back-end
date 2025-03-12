import { PartialType } from '@nestjs/mapped-types';
import {
  IsBoolean,
  IsNotEmpty,
  IsNumber,
  IsOptional,
  IsString,
} from 'class-validator';

export class CreateClickDto {
  @IsNotEmpty()
  @IsString()
  gclid: string;

  @IsNotEmpty()
  @IsString()
  ip: string;

  @IsNotEmpty()
  @IsString()
  customerId: string;

  @IsNotEmpty()
  location: object;

  @IsNotEmpty()
  @IsString()
  userAgent: string;

  @IsOptional()
  @IsString()
  referrer?: string;

  @IsOptional()
  @IsString()
  adId?: string;

  @IsOptional()
  @IsString()
  adGroupId?: string;

  @IsOptional()
  @IsString()
  campaignId?: string;
}

// Automatically make all properties optional
export class UpdateClickDto extends PartialType(CreateClickDto) {
  @IsOptional()
  @IsBoolean()
  isFraudulent?: boolean;

  @IsOptional()
  @IsNumber()
  sessionTime?: number;
}
