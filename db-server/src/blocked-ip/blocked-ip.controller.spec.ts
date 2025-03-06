import { Test, TestingModule } from '@nestjs/testing';
import { BlockedIpController } from './blocked-ip.controller';

describe('BlockedIpController', () => {
  let controller: BlockedIpController;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      controllers: [BlockedIpController],
    }).compile();

    controller = module.get<BlockedIpController>(BlockedIpController);
  });

  it('should be defined', () => {
    expect(controller).toBeDefined();
  });
});
