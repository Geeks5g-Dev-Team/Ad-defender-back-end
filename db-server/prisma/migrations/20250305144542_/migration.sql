/*
  Warnings:

  - Made the column `userId` on table `BlockedIp` required. This step will fail if there are existing NULL values in that column.

*/
-- DropForeignKey
ALTER TABLE "BlockedIp" DROP CONSTRAINT "BlockedIp_userId_fkey";

-- AlterTable
ALTER TABLE "BlockedIp" ALTER COLUMN "userId" SET NOT NULL;

-- AddForeignKey
ALTER TABLE "BlockedIp" ADD CONSTRAINT "BlockedIp_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
