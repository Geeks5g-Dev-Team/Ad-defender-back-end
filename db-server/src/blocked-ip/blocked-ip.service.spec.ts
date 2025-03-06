import { Test, TestingModule } from '@nestjs/testing';
import { BlockedIpService } from './blocked-ip.service';

describe('BlockedIpService', () => {
  let service: BlockedIpService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [BlockedIpService],
    }).compile();

    service = module.get<BlockedIpService>(BlockedIpService);
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });
});
